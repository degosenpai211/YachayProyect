"""Groq: mismo rol que Claude (cerebro del agente), gratis y sin tarjeta.

No hay "entrenamiento": es un modelo ya entrenado (Llama 3.3) al que solo
le mandamos instrucciones (prompt) por API, igual que a Claude.
"""

import json
import logging

import httpx

from app.config import get_settings

logger = logging.getLogger("yachay.groq")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


async def call_groq(system_prompt: str, user_payload: dict) -> str | None:
    settings = get_settings()
    if not settings.has_groq:
        return None

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": json.dumps(user_payload, ensure_ascii=False),
                        },
                    ],
                    "temperature": 0.4,
                    "max_tokens": 500,
                    "response_format": {"type": "json_object"},
                },
            )
            if resp.status_code >= 400:
                logger.warning("Groq respondió %s: %s", resp.status_code, resp.text[:300])
                return None
            data = resp.json()
            choices = data.get("choices") or []
            if not choices:
                logger.warning("Groq respondió sin choices: %s", data)
                return None
            return choices[0]["message"]["content"]
    except Exception:
        logger.exception("Fallo llamando a Groq")
        return None
