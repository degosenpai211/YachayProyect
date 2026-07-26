import httpx

from app.config import get_settings


async def speech_to_text(audio_url: str) -> str | None:
    """Transcribe audio remoto. Si falla o no hay clave, retorna None."""
    settings = get_settings()
    if not settings.has_elevenlabs or not audio_url:
        return None

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            audio_resp = await client.get(audio_url)
            audio_resp.raise_for_status()
            files = {"file": ("audio.ogg", audio_resp.content, "application/octet-stream")}
            # Endpoint STT de ElevenLabs (Creative / speech-to-text)
            stt = await client.post(
                "https://api.elevenlabs.io/v1/speech-to-text",
                headers={"xi-api-key": settings.elevenlabs_api_key},
                files=files,
                data={"model_id": "scribe_v1"},
            )
            if stt.status_code >= 400:
                return None
            data = stt.json()
            return (data.get("text") or data.get("transcript") or "").strip() or None
    except Exception:
        return None


async def text_to_speech(text: str) -> bytes | None:
    settings = get_settings()
    if not settings.has_elevenlabs or not settings.elevenlabs_voice_id:
        return None

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{settings.elevenlabs_voice_id}",
                headers={
                    "xi-api-key": settings.elevenlabs_api_key,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                },
                json={"text": text, "model_id": "eleven_multilingual_v2"},
            )
            if resp.status_code >= 400:
                return None
            return resp.content
    except Exception:
        return None
