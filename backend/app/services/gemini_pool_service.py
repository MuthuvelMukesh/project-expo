"""
Gemini key-pool client with graceful degradation and retry failover.
Optimized with connection pooling and improved error handling.
"""

import logging
from typing import Optional

import httpx

from app.core.config import get_settings

settings = get_settings()
log = logging.getLogger("campusiq.gemini_pool")

# Shared HTTP client with connection pooling for better performance
_http_client: Optional[httpx.AsyncClient] = None


def _get_http_client() -> httpx.AsyncClient:
    """Get or create a shared HTTP client with connection pooling."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            http2=True,  # Enable HTTP/2 for better performance
        )
    return _http_client


async def close_http_client():
    """Close the shared HTTP client. Call this on app shutdown."""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


class GeminiPoolError(Exception):
    def __init__(self, code: str, message: str, retry_eta_seconds: int = 60):
        self.code = code
        self.message = message
        self.retry_eta_seconds = retry_eta_seconds
        super().__init__(message)


class GeminiPoolClient:
    """Module-isolated Gemini API key pool with retry across keys."""

    @staticmethod
    def _module_keys(module: str) -> list[str]:
        pool = settings.GEMINI_KEY_POOLS.get(module, [])
        if pool:
            return pool
        if settings.GOOGLE_API_KEY:
            return [settings.GOOGLE_API_KEY]
        return []

    @staticmethod
    async def generate_json(module: str, prompt: str, timeout: float = 25.0) -> dict:
        keys = GeminiPoolClient._module_keys(module)
        if not keys:
            raise GeminiPoolError(
                code="NO_KEYS_CONFIGURED",
                message=f"No Gemini keys configured for module '{module}'.",
                retry_eta_seconds=settings.GEMINI_RETRY_ETA_SECONDS,
            )

        last_status: Optional[int] = None
        client = _get_http_client()
        
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
                "generationConfig": {"temperature": 0.1, "topP": 0.95, "topK": 40},
            }

            try:
                response = await client.post(endpoint, json=payload, timeout=timeout)

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
            except Exception as e:
                log.debug(f"Unexpected error with key in module '{module}': {e}")
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
        Generate a conversational (prose) response via Gemini.
        Returns the response text string.
        Raises GeminiPoolError if all keys are exhausted.
        """
        keys = GeminiPoolClient._module_keys(module)
        if not keys:
            raise GeminiPoolError(
                code="NO_KEYS_CONFIGURED",
                message=f"No Gemini keys configured for module '{module}'.",
                retry_eta_seconds=settings.GEMINI_RETRY_ETA_SECONDS,
            )

        last_status: Optional[int] = None
        client = _get_http_client()
        
        for key in keys:
            endpoint = (
                f"{settings.GOOGLE_BASE_URL}/models/{settings.GOOGLE_MODEL}:generateContent"
                f"?key={key}"
            )
            payload = {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": user_message}]}],
                "generationConfig": {
                    "temperature": temperature, 
                    "topP": 0.95, 
                    "topK": 40,
                    "maxOutputTokens": 1024,
                },
            }

            try:
                response = await client.post(endpoint, json=payload, timeout=timeout)

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
            except Exception as e:
                log.debug(f"Unexpected error with key in module '{module}': {e}")
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
