"""
CampusIQ LLM Client

Supports two providers (set via LLM_PROVIDER env var):
  • "openrouter"  — OpenAI-compatible proxy (default)
  • "gemini"      — Google Gemini native API (via its OpenAI-compat endpoint)

One API key. Simple retry. Clean errors.
Used by: chatbot, NLP CRUD, conversational ops, predictions.
"""

import httpx
import asyncio
import json
import re
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Persistent async HTTP client — reused across requests
_http_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    """Get or create the shared async HTTP client."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=60.0)
    return _http_client


def _get_api_url() -> str:
    """Return the chat completions URL based on the configured provider."""
    if settings.LLM_PROVIDER == "gemini":
        return f"{settings.GEMINI_BASE_URL}/chat/completions"
    return f"{settings.OPENROUTER_BASE_URL}/chat/completions"


def _get_headers() -> dict:
    """Return auth headers appropriate for the configured provider."""
    headers = {
        "Authorization": f"Bearer {settings.GEMINI_API_KEY}",
        "Content-Type": "application/json",
    }
    # OpenRouter needs extra headers for attribution
    if settings.LLM_PROVIDER != "gemini":
        headers["HTTP-Referer"] = "https://campusiq.edu"
        headers["X-Title"] = "CampusIQ"
    return headers


def _provider_label() -> str:
    """Human label for log messages."""
    return "Gemini" if settings.LLM_PROVIDER == "gemini" else "OpenRouter"


class GeminiError(Exception):
    """Raised when LLM API call fails after all retries."""
    pass


class GeminiClient:
    """
    Unified LLM client for CampusIQ.
    Talks to OpenRouter or Google Gemini (both OpenAI-compatible).
    All methods are async. Uses httpx for non-blocking HTTP calls.
    """

    @classmethod
    async def _call(
        cls,
        prompt: str,
        system_instruction: str,
        temperature: float,
        json_mode: bool = False
    ) -> str:
        """
        Core LLM API call with exponential backoff retry.
        Works with both OpenRouter and native Gemini.
        """
        last_error = None
        client = _get_client()
        api_url = _get_api_url()
        headers = _get_headers()
        label = _provider_label()

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ]

        payload = {
            "model": settings.GEMINI_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": settings.GEMINI_MAX_OUTPUT_TOKENS,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        for attempt in range(settings.GEMINI_MAX_RETRIES):
            try:
                resp = await client.post(api_url, json=payload, headers=headers)

                if resp.status_code == 429:
                    wait = settings.GEMINI_RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"[{label}] Rate limited, retrying in {wait}s (attempt {attempt + 1}/{settings.GEMINI_MAX_RETRIES})")
                    await asyncio.sleep(wait)
                    continue

                if resp.status_code >= 400:
                    error_text = resp.text[:300]
                    raise GeminiError(f"{label} API error {resp.status_code}: {error_text}")

                data = resp.json()

                if "error" in data:
                    raise GeminiError(f"{label} error: {data['error']}")

                choice = data["choices"][0]["message"]
                text = choice.get("content") or ""

                # Some free models put output in reasoning field
                if not text.strip() and choice.get("reasoning"):
                    text = choice["reasoning"]

                if not text or not text.strip():
                    raise GeminiError("LLM returned empty response")

                return text.strip()

            except GeminiError:
                raise
            except Exception as e:
                last_error = e
                err = str(e).lower()
                is_rate_limit = any(x in err for x in ["quota", "429", "rate", "resource exhausted"])

                if is_rate_limit and attempt < settings.GEMINI_MAX_RETRIES - 1:
                    wait = settings.GEMINI_RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"[{label}] Rate limit, retrying in {wait}s (attempt {attempt + 1}/{settings.GEMINI_MAX_RETRIES})")
                    await asyncio.sleep(wait)
                    continue

                if attempt < settings.GEMINI_MAX_RETRIES - 1:
                    await asyncio.sleep(settings.GEMINI_RETRY_DELAY)
                    continue

                logger.error(f"[{label}] LLM failed after {settings.GEMINI_MAX_RETRIES} attempts: {e}")
                raise GeminiError(f"LLM API failed: {str(e)}")

        raise GeminiError(f"LLM API failed after all retries. Last: {last_error}")

    @classmethod
    async def ask_json(
        cls,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> dict:
        """
        Ask LLM and get back a parsed JSON dict.

        Used for:
        - NLP intent parsing (what does user want to do?)
        - Command Console operation extraction
        - Structured data extraction

        Returns: parsed dict
        Raises: GeminiError if API fails
                ValueError if response is not valid JSON
        """
        system = system_instruction or (
            "You are a JSON generator for a college ERP system. "
            "Return ONLY valid JSON. "
            "No markdown fences. No backticks. No explanation text. "
            "The entire response must be parseable by Python's json.loads()."
        )

        raw = await cls._call(
            prompt=prompt,
            system_instruction=system,
            temperature=settings.GEMINI_TEMPERATURE_JSON,
            json_mode=True
        )

        cleaned = cls._clean_json(raw)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            extracted = cls._extract_json(raw)
            if extracted:
                return extracted
            logger.error(f"Could not parse LLM JSON response: {raw[:300]}")
            raise ValueError(f"LLM returned invalid JSON: {raw[:200]}")

    @classmethod
    async def ask(
        cls,
        user_message: str,
        system_prompt: str,
        conversation_history: Optional[list[dict]] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Ask LLM and get back a plain text response.

        Used for:
        - Chatbot conversations
        - Natural language responses to user queries
        - Explanations and summaries

        conversation_history format:
          [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

        Returns: string response
        Raises: GeminiError if API fails
        """
        temp = temperature if temperature is not None else settings.GEMINI_TEMPERATURE_CHAT

        if conversation_history and len(conversation_history) > 0:
            history_lines = []
            for msg in conversation_history[-10:]:
                role_label = "User" if msg["role"] == "user" else "Assistant"
                history_lines.append(f"{role_label}: {msg['content']}")
            history_text = "\n".join(history_lines)
            full_prompt = f"Previous conversation:\n{history_text}\n\nUser: {user_message}"
        else:
            full_prompt = user_message

        return await cls._call(
            prompt=full_prompt,
            system_instruction=system_prompt,
            temperature=temp,
            json_mode=False
        )

    @classmethod
    async def ask_with_gemini_history(
        cls,
        messages: list[dict],
        system_prompt: str,
        temperature: Optional[float] = None
    ) -> str:
        """
        Ask LLM using multi-turn conversation.

        messages format (Gemini native — converted to OpenAI format):
          [{"role": "user", "parts": ["text"]}, {"role": "model", "parts": ["text"]}]

        Used for multi-turn chatbot where conversation memory matters.
        Returns: string response
        """
        temp = temperature if temperature is not None else settings.GEMINI_TEMPERATURE_CHAT

        # Convert Gemini-style messages to OpenAI-style
        openai_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            role = "assistant" if msg["role"] == "model" else "user"
            content = msg["parts"][0] if isinstance(msg["parts"], list) else msg["parts"]
            openai_messages.append({"role": role, "content": content})

        last_error = None
        client = _get_client()
        api_url = _get_api_url()
        headers = _get_headers()
        label = _provider_label()

        payload = {
            "model": settings.GEMINI_MODEL,
            "messages": openai_messages,
            "temperature": temp,
            "max_tokens": settings.GEMINI_MAX_OUTPUT_TOKENS,
        }

        for attempt in range(settings.GEMINI_MAX_RETRIES):
            try:
                resp = await client.post(api_url, json=payload, headers=headers)

                if resp.status_code == 429:
                    await asyncio.sleep(settings.GEMINI_RETRY_DELAY * (2 ** attempt))
                    continue

                if resp.status_code >= 400:
                    raise GeminiError(f"{label} error {resp.status_code}: {resp.text[:300]}")

                data = resp.json()
                if "error" in data:
                    raise GeminiError(f"{label} error: {data['error']}")

                choice = data["choices"][0]["message"]
                text = choice.get("content") or ""
                if not text.strip() and choice.get("reasoning"):
                    text = choice["reasoning"]

                return text.strip()

            except GeminiError:
                raise
            except Exception as e:
                last_error = e
                if attempt < settings.GEMINI_MAX_RETRIES - 1:
                    await asyncio.sleep(settings.GEMINI_RETRY_DELAY)
                    continue
                raise GeminiError(f"LLM chat failed: {str(e)}")

        raise GeminiError(f"LLM chat failed after all retries. Last: {last_error}")

    @classmethod
    async def health_check(cls) -> dict:
        """
        Verify LLM API key is working.
        """
        try:
            response = await cls.ask(
                user_message="Reply with exactly: OK",
                system_prompt="Reply with exactly what the user says.",
                temperature=0.0
            )
            return {
                "status": "healthy",
                "provider": settings.LLM_PROVIDER,
                "model": settings.GEMINI_MODEL,
                "response": response.strip()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": settings.LLM_PROVIDER,
                "model": settings.GEMINI_MODEL,
                "error": str(e)
            }

    @staticmethod
    def _clean_json(text: str) -> str:
        """Strip markdown code fences from LLM response."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            start = 1
            end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
            text = "\n".join(lines[start:end])
        return text.strip()

    @staticmethod
    def _extract_json(text: str) -> Optional[dict]:
        """Extract first JSON object found in text."""
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None


async def close_http_client():
    """Close the shared HTTP client on shutdown."""
    global _http_client
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None
