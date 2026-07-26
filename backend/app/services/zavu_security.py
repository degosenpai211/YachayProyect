"""Verificación de firmas HMAC de webhooks Zavu (X-Zavu-Signature)."""

from __future__ import annotations

import hashlib
import hmac
import logging
import time

logger = logging.getLogger("yachay.zavu_security")

# Rechazar firmas más viejas que 5 minutos (anti-replay), igual que docs Zavu.
MAX_AGE_SECONDS = 300


def verify_zavu_signature(signature_header: str | None, raw_body: bytes, secret: str) -> bool:
    """Valida `X-Zavu-Signature: t=<unix>,v1=<hex>` según docs.zavu.dev."""
    if not secret or not signature_header or not raw_body:
        return False

    timestamp_str: str | None = None
    signature: str | None = None
    for part in signature_header.split(","):
        part = part.strip()
        if part.startswith("t="):
            timestamp_str = part[2:]
        elif part.startswith("v1="):
            signature = part[3:]

    if not timestamp_str or not signature:
        return False

    try:
        timestamp = int(timestamp_str)
    except ValueError:
        return False

    now = int(time.time())
    if abs(now - timestamp) > MAX_AGE_SECONDS:
        logger.warning("Webhook Zavu con timestamp fuera de ventana (t=%s now=%s)", timestamp, now)
        return False

    signed_payload = f"{timestamp}.".encode("utf-8") + raw_body
    expected = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    try:
        return hmac.compare_digest(expected, signature)
    except (TypeError, ValueError):
        return False
