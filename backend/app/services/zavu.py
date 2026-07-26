import logging

import httpx

from app.config import get_settings

logger = logging.getLogger("yachay.zavu")


async def send_message(to: str, text: str) -> bool:
    """Envía respuesta por Zavu. En demo/sin clave, solo log lógico (True)."""
    settings = get_settings()
    if not settings.has_zavu:
        return True
    if not to or not text:
        logger.warning("send_message llamado sin destinatario o texto (to=%r)", to)
        return False

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                settings.zavu_send_url,
                headers={
                    "Authorization": f"Bearer {settings.zavu_api_key}",
                    "Content-Type": "application/json",
                },
                # La API de Zavu espera el campo "text", no "message".
                json={"to": to, "text": text, "channel": "telegram"},
            )
            if resp.status_code >= 400:
                logger.warning("Zavu respondió %s al enviar mensaje: %s", resp.status_code, resp.text[:300])
            return resp.status_code < 400
    except Exception:
        logger.exception("Fallo enviando mensaje via Zavu")
        return False
