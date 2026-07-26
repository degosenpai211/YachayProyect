from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.services.media_store import get_audio

router = APIRouter(tags=["media"])


@router.get("/media/tts/{token}.mp3")
def serve_tts_audio(token: str):
    data = get_audio(token)
    if not data:
        raise HTTPException(status_code=404, detail="Audio no encontrado o expirado")
    return Response(
        content=data,
        media_type="audio/mpeg",
        headers={"Cache-Control": "public, max-age=300"},
    )
