import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ChatProcessResult, ZavuWebhookIn
from app.services.agent import DONE_RE, extract_student_code, process_student_message
from app.services.elevenlabs_svc import speech_to_text
from app.services.zavu import send_message

logger = logging.getLogger("yachay.webhook")

router = APIRouter(tags=["webhook"])


def _should_send_thinking_ack(text: str) -> bool:
    """Ack corto antes de Groq (latencia percibida), salvo flujos rápidos."""
    if not text or len(text.strip()) < 6:
        return False
    if text.lower().startswith("/start"):
        return False
    if extract_student_code(text) and len(text.split()) <= 2:
        return False
    if DONE_RE.search(text.strip()):
        return False
    return True


@router.post("/webhook", response_model=ChatProcessResult)
async def zavu_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    # Auth de webhook DESACTIVADA temporalmente para el hackathon.
    raw_body = await request.body()

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
        await send_message(sender, "Un momento, estoy escuchando tu audio… ⏳")
        transcribed = await speech_to_text(audio_url)
        if transcribed:
            text = transcribed
        else:
            result = ChatProcessResult(
                reply="No pude oír el audio. Escríbeme la duda por texto, por favor.",
            )
            await send_message(sender, result.reply)
            return result

    if _should_send_thinking_ack(text or ""):
        await send_message(sender, "Un momento, estoy pensando tu duda… ⏳")

    result = await process_student_message(db, sender=sender, text=text)
    await send_message(sender, result.reply)
    return result


@router.post("/webhook/simulate", response_model=ChatProcessResult)
async def simulate_chat(payload: dict, db: Session = Depends(get_db)):
    """Para Postman/curl mientras Zavu no está listo."""
    sender = str(payload.get("telegram_id") or payload.get("from") or "demo_user")
    text = str(payload.get("message") or payload.get("text") or "")
    return await process_student_message(db, sender=sender, text=text)
