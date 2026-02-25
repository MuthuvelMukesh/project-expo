"""
Gemini key-pool client with graceful degradation and retry failover.
"""

import logging
from typing import Optional

import httpx

from app.core.config import get_settings

settings = get_settings()
log = logging.getLogger("campusiq.gemini_pool")


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
