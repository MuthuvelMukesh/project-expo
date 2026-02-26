"""
LLM client with OpenRouter (primary) and Gemini (fallback) support.
"""

import logging
from typing import Optional

import httpx

from app.core.config import get_settings

settings = get_settings()
log = logging.getLogger("campusiq.llm_pool")


class GeminiPoolError(Exception):
    def __init__(self, code: str, message: str, retry_eta_seconds: int = 60):
        self.code = code
        self.message = message
        self.retry_eta_seconds = retry_eta_seconds
        super().__init__(message)


class GeminiPoolClient:
    """LLM client that uses OpenRouter (if configured) or Gemini as fallback."""

    @staticmethod
    def _use_openrouter() -> bool:
        """Check if OpenRouter is configured and should be used."""
        return bool(settings.OPENROUTER_API_KEY)

    @staticmethod
    def _module_keys(module: str) -> list[str]:
        pool = settings.GEMINI_KEY_POOLS.get(module, [])
        if pool:
            return pool
        if settings.GOOGLE_API_KEY:
            return [settings.GOOGLE_API_KEY]
        return []

    @staticmethod
    async def _openrouter_request(
        system_prompt: str,
        user_message: str,
        temperature: float = 0.1,
        timeout: float = 30.0,
        json_mode: bool = False,
    ) -> dict:
        """Make a request to OpenRouter API (OpenAI-compatible format)."""
        endpoint = f"{settings.OPENROUTER_BASE_URL}/chat/completions"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})
        
        payload = {
            "model": settings.OPENROUTER_MODEL,
            "messages": messages,
            "temperature": temperature,
        }
        
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://campusiq.edu",
            "X-Title": "CampusIQ",
        }
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "").strip()
                    return {"ok": True, "text": content}
                return {"ok": False, "error": "No response content"}
            
            log.warning(f"OpenRouter error: {response.status_code} - {response.text[:200]}")
            return {"ok": False, "error": f"HTTP {response.status_code}"}
            
        except Exception as e:
            log.error(f"OpenRouter request failed: {e}")
            return {"ok": False, "error": str(e)}

    @staticmethod
    async def generate_json(module: str, prompt: str, timeout: float = 25.0) -> dict:
        # Try OpenRouter first if configured
        if GeminiPoolClient._use_openrouter():
            system = "You are a helpful AI assistant. Return only valid JSON. No markdown code blocks, no commentary, just raw JSON."
            result = await GeminiPoolClient._openrouter_request(
                system_prompt=system,
                user_message=prompt,
                temperature=0.1,
                timeout=timeout,
                json_mode=True,
            )
            if result.get("ok"):
                return result
            log.warning(f"OpenRouter failed, trying Gemini fallback: {result.get('error')}")
        
        # Fallback to Gemini
        keys = GeminiPoolClient._module_keys(module)
        if not keys:
            if GeminiPoolClient._use_openrouter():
                raise GeminiPoolError(
                    code="LLM_UNAVAILABLE",
                    message="OpenRouter request failed and no Gemini keys configured.",
                    retry_eta_seconds=settings.GEMINI_RETRY_ETA_SECONDS,
                )
            raise GeminiPoolError(
                code="NO_KEYS_CONFIGURED",
                message=f"No LLM keys configured for module '{module}'.",
                retry_eta_seconds=settings.GEMINI_RETRY_ETA_SECONDS,
            )

        last_status: Optional[int] = None
        for key in keys:
            endpoint = (
                f"{settings.GOOGLE_BASE_URL}/models/{settings.GOOGLE_MODEL}:generateContent"
                f"?key={key}"
            )
            payload = {
                "systemInstruction": {
                    "parts": [
                        {"text": "Return only strict JSON. No markdown. No commentary."}
                    ]
                },
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1},
            }

            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(endpoint, json=payload)

                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates") or []
                    if not candidates:
                        continue
                    parts = candidates[0].get("content", {}).get("parts", [])
                    content = "".join(part.get("text", "") for part in parts).strip()
                    return {"ok": True, "text": content}

                last_status = response.status_code
                if response.status_code in (429, 500, 502, 503, 504):
                    continue

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError):
                continue
            except Exception:
                continue

        retry_eta = settings.GEMINI_RETRY_ETA_SECONDS
        if last_status == 429:
            code = "RATE_LIMITED"
            msg = "All Gemini keys for this module are rate-limited."
        else:
            code = "SERVICE_UNAVAILABLE"
            msg = "Gemini service unavailable for this module."

        log.warning("Gemini pool exhausted for module=%s code=%s", module, code)
        raise GeminiPoolError(code=code, message=msg, retry_eta_seconds=retry_eta)

    @staticmethod
    async def generate_text(
        module: str,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.4,
        timeout: float = 30.0,
    ) -> str:
        """
        Generate a conversational (prose) response.
        Uses OpenRouter if configured, otherwise falls back to Gemini.
        Returns the response text string.
        Raises GeminiPoolError if all backends are exhausted.
        """
        # Try OpenRouter first if configured
        if GeminiPoolClient._use_openrouter():
            result = await GeminiPoolClient._openrouter_request(
                system_prompt=system_prompt,
                user_message=user_message,
                temperature=temperature,
                timeout=timeout,
            )
            if result.get("ok"):
                return result["text"]
            log.warning(f"OpenRouter failed for text gen, trying Gemini: {result.get('error')}")
        
        # Fallback to Gemini
        keys = GeminiPoolClient._module_keys(module)
        if not keys:
            if GeminiPoolClient._use_openrouter():
                raise GeminiPoolError(
                    code="LLM_UNAVAILABLE",
                    message="OpenRouter request failed and no Gemini keys configured.",
                    retry_eta_seconds=settings.GEMINI_RETRY_ETA_SECONDS,
                )
            raise GeminiPoolError(
                code="NO_KEYS_CONFIGURED",
                message=f"No LLM keys configured for module '{module}'.",
                retry_eta_seconds=settings.GEMINI_RETRY_ETA_SECONDS,
            )

        last_status: Optional[int] = None
        for key in keys:
            endpoint = (
                f"{settings.GOOGLE_BASE_URL}/models/{settings.GOOGLE_MODEL}:generateContent"
                f"?key={key}"
            )
            payload = {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": user_message}]}],
                "generationConfig": {"temperature": temperature},
            }

            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(endpoint, json=payload)

                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates") or []
                    if not candidates:
                        continue
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in parts).strip()
                    if text:
                        return text
                    continue

                last_status = response.status_code
                if response.status_code in (429, 500, 502, 503, 504):
                    continue

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError):
                continue
            except Exception:
                continue

        retry_eta = settings.GEMINI_RETRY_ETA_SECONDS
        code = "RATE_LIMITED" if last_status == 429 else "SERVICE_UNAVAILABLE"
        msg = (
            "All Gemini keys for this module are rate-limited."
            if last_status == 429
            else "Gemini service unavailable for this module."
        )
        log.warning("Gemini text pool exhausted for module=%s code=%s", module, code)
        raise GeminiPoolError(code=code, message=msg, retry_eta_seconds=retry_eta)
