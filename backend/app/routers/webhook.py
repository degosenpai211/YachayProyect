import json
import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas import ChatProcessResult, ZavuWebhookIn
from app.services.agent import DONE_RE, extract_student_code, process_student_message
from app.services.elevenlabs_svc import speech_to_text, text_to_speech
from app.services.media_store import put_audio
from app.services.zavu import send_audio, send_message

logger = logging.getLogger("yachay.webhook")

router = APIRouter(tags=["webhook"])

AUDIO_REQUEST_RE = re.compile(
    r"\b(audio|voz|nota\s+de\s+voz|en\s+audio|por\s+voz|háblame|hablame|escuchar)\b",
    re.IGNORECASE,
)


def _should_send_thinking_ack(text: str) -> bool:
    if not text or len(text.strip()) < 6:
        return False
    if text.lower().startswith("/start"):
        return False
    if extract_student_code(text) and len(text.split()) <= 2:
        return False
    if DONE_RE.search(text.strip()):
        return False
    return True


def _wants_voice_reply(text: str, had_inbound_audio: bool) -> bool:
    """Voz de vuelta si mandó nota de voz o pidió audio explícitamente."""
    if had_inbound_audio:
        return True
    return bool(text and AUDIO_REQUEST_RE.search(text))


def _tts_clean(text: str) -> str:
    cleaned = re.sub(r"[*_`#]+", "", text or "")
    cleaned = re.sub(r"\n{2,}", ". ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # ElevenLabs: mantener clips cortos para latencia/créditos
    if len(cleaned) > 700:
        cleaned = cleaned[:697].rsplit(" ", 1)[0] + "…"
    return cleaned


def _public_base(request: Request) -> str:
    settings = get_settings()
    if settings.public_base_url.strip():
        return settings.public_base_url.strip().rstrip("/")
    base = str(request.base_url).rstrip("/")
    if base.startswith("http://"):
        base = "https://" + base[len("http://") :]
    return base


async def _maybe_send_voice(request: Request, to: str, reply: str) -> bool:
    settings = get_settings()
    if not settings.has_elevenlabs_tts:
        logger.warning("TTS pedido pero falta ELEVENLABS_API_KEY o ELEVENLABS_VOICE_ID")
        return False
    spoken = _tts_clean(reply)
    if not spoken:
        return False
    audio = await text_to_speech(spoken)
    if not audio:
        return False
    token = put_audio(audio)
    media_url = f"{_public_base(request)}/media/tts/{token}.mp3"
    logger.info("Enviando TTS mediaUrl=%s bytes=%s", media_url, len(audio))
    return await send_audio(to, media_url)


@router.post("/webhook", response_model=ChatProcessResult)
async def zavu_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
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
    had_inbound_audio = bool(audio_url)

    if not sender or sender == "anon":
        logger.warning("Webhook Zavu sin remitente identificable: %s", payload)
        return ChatProcessResult(reply="")

    logger.info("Webhook inbound sender=%s text_len=%s has_audio=%s", sender, len(text or ""), had_inbound_audio)

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

    wants_voice = _wants_voice_reply(text or "", had_inbound_audio)

    if _should_send_thinking_ack(text or ""):
        if wants_voice:
            await send_message(sender, "Un momento, preparo la explicación (también en audio)… ⏳")
        else:
            await send_message(sender, "Un momento, estoy pensando tu duda… ⏳")

    result = await process_student_message(db, sender=sender, text=text)
    await send_message(sender, result.reply)

    if wants_voice and result.reply:
        ok = await _maybe_send_voice(request, sender, result.reply)
        if not ok:
            await send_message(
                sender,
                "(No pude generar el audio ahora; arriba va la explicación en texto.)",
            )

    return result


@router.post("/webhook/simulate", response_model=ChatProcessResult)
async def simulate_chat(payload: dict, db: Session = Depends(get_db)):
    """Para Postman/curl mientras Zavu no está listo."""
    sender = str(payload.get("telegram_id") or payload.get("from") or "demo_user")
    text = str(payload.get("message") or payload.get("text") or "")
    return await process_student_message(db, sender=sender, text=text)
