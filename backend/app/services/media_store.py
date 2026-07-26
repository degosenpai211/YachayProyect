"""Almacén temporal en memoria para MP3 de TTS (URL pública para Zavu)."""

from __future__ import annotations

import time
import uuid
from threading import Lock

_TTL_SECONDS = 600  # 10 min
_lock = Lock()
_store: dict[str, tuple[bytes, float]] = {}


def put_audio(data: bytes) -> str:
    token = uuid.uuid4().hex
    with _lock:
        _purge_locked()
        _store[token] = (data, time.time() + _TTL_SECONDS)
    return token


def get_audio(token: str) -> bytes | None:
    with _lock:
        _purge_locked()
        item = _store.get(token)
        if not item:
            return None
        data, expires = item
        if time.time() > expires:
            _store.pop(token, None)
            return None
        return data


def _purge_locked() -> None:
    now = time.time()
    dead = [k for k, (_, exp) in _store.items() if now > exp]
    for k in dead:
        _store.pop(k, None)
