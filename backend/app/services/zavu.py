import httpx

from app.config import get_settings


async def send_message(to: str, text: str) -> bool:
    """Envía respuesta por Zavu. En demo/sin clave, solo log lógico (True)."""
    settings = get_settings()
    if not settings.has_zavu:
        return True

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                settings.zavu_send_url,
                headers={
                    "Authorization": f"Bearer {settings.zavu_api_key}",
                    "Content-Type": "application/json",
                },
                json={"to": to, "message": text, "channel": "telegram"},
            )
            return resp.status_code < 400
    except Exception:
        return False
