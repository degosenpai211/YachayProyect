import logging

import httpx

from app.config import get_settings

logger = logging.getLogger("yachay.exa")


async def ground_bolivian_example(topic_label: str, question: str) -> str | None:
    """Busca un dato/ejemplo; timeout corto. Si falla, None."""
    settings = get_settings()
    if not settings.has_exa:
        return None

    query = f"ejemplo Bolivia ciencia escolar {topic_label} {question}"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(
                "https://api.exa.ai/search",
                headers={
                    "x-api-key": settings.exa_api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "query": query,
                    "num_results": 2,
                    "type": "auto",
                    "contents": {"text": {"max_characters": 300}},
                },
            )
            if resp.status_code >= 400:
                logger.warning("Exa respondió %s: %s", resp.status_code, resp.text[:300])
                return None
            results = resp.json().get("results") or []
            if not results:
                return None
            first = results[0]
            snippet = (first.get("text") or first.get("title") or "").strip()
            return snippet[:280] if snippet else None
    except Exception:
        logger.exception("Fallo consultando Exa")
        return None
