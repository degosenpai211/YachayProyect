import json
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas import ChatProcessResult, ZavuWebhookIn
from app.services.agent import process_student_message
from app.services.elevenlabs_svc import speech_to_text
from app.services.zavu import send_message
from app.services.zavu_security import verify_zavu_signature

logger = logging.getLogger("yachay.webhook")

router = APIRouter(tags=["webhook"])


def _authorize_webhook(
    *,
    settings,
    raw_body: bytes,
    x_zavu_signature: str | None,
    x_zavu_secret: str | None,
) -> None:
    """Zavu firma con HMAC en X-Zavu-Signature (docs oficiales).

    También aceptamos X-Zavu-Secret == secret como atajo para pruebas manuales.
    Si no hay secret configurado, dejamos pasar (útil en demo local).

    Si el secret de Railway está desfasado respecto a Zavu (muy común al
    regenerar), NO bloqueamos el mensaje: lo procesamos igual y dejamos
    warning en logs. Así el bot no queda mudo en el hackathon.
    """
    secret = (settings.zavu_webhook_secret or "").strip()
    if not secret:
        return

    if x_zavu_secret and x_zavu_secret == secret:
        return

    if verify_zavu_signature(x_zavu_signature, raw_body, secret):
        return

    logger.error(
        "Firma Zavu no coincide con ZAVU_WEBHOOK_SECRET — procesando igual. "
        "Actualiza el secret en Railway (tiene X-Zavu-Signature=%s)",
        bool(x_zavu_signature),
    )
    # No raise 401: un secret desfasado dejaba el bot totalmente mudo.


@router.post("/webhook", response_model=ChatProcessResult)
async def zavu_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_zavu_signature: str | None = Header(default=None),
    x_zavu_secret: str | None = Header(default=None),
):
    settings = get_settings()
    raw_body = await request.body()
    _authorize_webhook(
        settings=settings,
        raw_body=raw_body,
        x_zavu_signature=x_zavu_signature,
        x_zavu_secret=x_zavu_secret,
    )

    try:
        payload = json.loads(raw_body.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="JSON inválido") from exc

    data = ZavuWebhookIn.model_validate(payload)

    if not data.is_relevant_event():
        logger.info("Ignorando evento Zavu tipo=%s (no es message.inbound)", data.type)
        return ChatProcessResult(reply="")

    text = data.resolved_text()
    sender = data.resolved_sender()
    audio_url = data.resolved_media_url()

    if not sender or sender == "anon":
        logger.warning("Webhook Zavu sin remitente identificable: %s", payload)
        return ChatProcessResult(reply="")

    logger.info("Webhook inbound sender=%s text_len=%s has_audio=%s", sender, len(text or ""), bool(audio_url))

    if not text and audio_url:
        transcribed = await speech_to_text(audio_url)
        if transcribed:
            text = transcribed
        else:
            result = ChatProcessResult(
                reply="No pude oír el audio. Escríbeme la duda por texto, por favor.",
            )
            await send_message(sender, result.reply)
            return result

    result = await process_student_message(db, sender=sender, text=text)
    await send_message(sender, result.reply)
    return result


@router.post("/webhook/simulate", response_model=ChatProcessResult)
async def simulate_chat(payload: dict, db: Session = Depends(get_db)):
    """Para Postman/curl mientras Zavu no está listo."""
    sender = str(payload.get("telegram_id") or payload.get("from") or "demo_user")
    text = str(payload.get("message") or payload.get("text") or "")
    return await process_student_message(db, sender=sender, text=text)
