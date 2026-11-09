"""Google Gemini AI Provider implementation."""

import json
from typing import Any, Dict, Optional
import httpx
from app.ai.provider import AIProvider
from app.ai.fallback_provider import FallbackAIProvider
from app.core.config import settings
from app.core.logging import logger


class GeminiAIProvider(AIProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.AI_API_KEY
        self.model = model or settings.AI_MODEL or "gemini-1.5-flash"
        self.fallback = FallbackAIProvider()

    async def generate_structured_json(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        if not self.api_key:
            logger.info("Gemini API key not configured. Using deterministic fallback provider.")
            return await self.fallback.generate_structured_json(system_prompt, user_prompt, response_schema)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n\nUSER INPUT:\n{user_prompt}"}]}
            ],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
            },
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
                        return json.loads(text)
                logger.warning(f"Gemini API returned status {res.status_code}. Falling back to deterministic provider.")
                return await self.fallback.generate_structured_json(system_prompt, user_prompt, response_schema)
        except Exception as e:
            logger.warning(f"Error calling Gemini API: {e}. Falling back to deterministic provider.")
            return await self.fallback.generate_structured_json(system_prompt, user_prompt, response_schema)
