import logging

import httpx

from app.config import get_settings

logger = logging.getLogger("yachay.zavu")


def normalize_telegram_recipient(to: str) -> str:
    """Zavu a veces manda 'telegram:6115305475'; la API de envío espera el chat ID numérico."""
    value = (to or "").strip()
    if value.lower().startswith("telegram:"):
        value = value.split(":", 1)[1].strip()
    return value


async def send_message(to: str, text: str) -> bool:
    """Envía respuesta por Zavu. En demo/sin clave, solo log lógico (True)."""
    settings = get_settings()
    if not settings.has_zavu:
        return True
    recipient = normalize_telegram_recipient(to)
    if not recipient or not text:
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
                json={"to": recipient, "text": text, "channel": "telegram"},
            )
            if resp.status_code >= 400:
                logger.warning(
                    "Zavu respondió %s al enviar texto a %s: %s",
                    resp.status_code,
                    recipient,
                    resp.text[:300],
                )
            else:
                logger.info("Zavu texto OK a %s status=%s", recipient, resp.status_code)
            return resp.status_code < 400
    except Exception:
        logger.exception("Fallo enviando mensaje via Zavu")
        return False


async def send_audio(to: str, media_url: str) -> bool:
    """Envía audio (MP3) por Telegram vía Zavu. media_url debe ser HTTPS público."""
    settings = get_settings()
    if not settings.has_zavu:
        return True
    recipient = normalize_telegram_recipient(to)
    if not recipient or not media_url:
        logger.warning("send_audio sin destinatario o URL (to=%r)", to)
        return False

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                settings.zavu_send_url,
                headers={
                    "Authorization": f"Bearer {settings.zavu_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "to": recipient,
                    "channel": "telegram",
                    "messageType": "audio",
                    "content": {"mediaUrl": media_url},
                },
            )
            if resp.status_code >= 400:
                logger.warning(
                    "Zavu respondió %s al enviar audio a %s: %s",
                    resp.status_code,
                    recipient,
                    resp.text[:300],
                )
            else:
                logger.info("Zavu audio OK a %s status=%s", recipient, resp.status_code)
            return resp.status_code < 400
    except Exception:
        logger.exception("Fallo enviando audio via Zavu")
        return False
