import asyncio
import json
import logging
import re

from app.config import get_settings
from app.services.groq_svc import call_groq
from app.topics import TOPICS, classify_topic_heuristic, topic_label

logger = logging.getLogger("yachay.claude")

SYSTEM_PROMPT = """Eres Yachay, tutor escolar boliviano de ciencias para primaria/secundaria.
Responde en español claro, máximo 120 palabras.
Estructura SIEMPRE cuando el tema SÍ encaje:
1) Explicación breve
2) Un ejemplo boliviano concreto
3) Una pregunta de chequeo corta

Temas permitidos (usa exactamente estos ids en "topic"):
- densidad_flotacion
- fotosintesis
- estados_materia
- electricidad_basica
- sistema_digestivo

Si la duda NO encaja en esos temas:
- pon "topic": null
- en "reply" dilo amable y ofrece esos 5 temas (sin inventar otro topic_id)
- "off_topic": true

Si el alumno pide "en audio", "por voz" o "nota de voz": explica el tema IGUAL en texto normal.
NUNCA digas que no puedes enviar audio; el sistema convierte tu reply a voz aparte.
Evita markdown pesado (**negritas**) para que suene bien al leerse en voz alta.

Usa el historial reciente (si viene) para no repetir y seguir la conversación.

Responde SOLO JSON válido:
{
  "topic": "topic_id o null",
  "reply": "texto para el estudiante",
  "needs_experiment": true/false,
  "off_topic": true/false
}
"""


async def generate_tutor_reply(
    user_text: str,
    weakness: bool = False,
    topic_hint: str | None = None,
    history: list[dict] | None = None,
) -> dict:
    """Prioridad: Claude (si hay créditos) -> Groq (gratis) -> plantillas locales."""
    settings = get_settings()
    user_payload = {
        "pregunta": user_text,
        "topic_hint": topic_hint,
        "weakness": weakness,
        "topics": {k: v["label"] for k, v in TOPICS.items()},
        "historial": history or [],
    }

    raw: str | None = None

    if settings.has_claude:
        raw = await asyncio.to_thread(_call_claude, user_payload, settings.anthropic_api_key)

    if raw is None and settings.has_groq:
        raw = await call_groq(SYSTEM_PROMPT, user_payload)

    if raw is None:
        return _demo_reply(user_text, weakness, topic_hint)

    parsed = _extract_json(raw)
    if not parsed:
        return _demo_reply(user_text, weakness, topic_hint)

    topic = parsed.get("topic")
    off_topic = bool(parsed.get("off_topic"))
    if topic in ("null", "", "None"):
        topic = None
    if topic and topic not in TOPICS:
        # Id inválido del modelo: intentar heurística; si no, off-topic
        topic = classify_topic_heuristic(user_text)
        if not topic:
            off_topic = True

    # Si el modelo marca off_topic o deja topic null, NO forzar keyword match a ciegas
    # (evita clasificar mal "hola" o preguntas de historia).
    if off_topic or topic is None:
        if topic is None and not off_topic:
            # Sin señal clara: solo heurística como respaldo suave
            topic = classify_topic_heuristic(user_text)
        if topic is None:
            return {
                "topic": None,
                "reply": parsed.get("reply")
                or _demo_reply(user_text, weakness, topic_hint)["reply"],
                "needs_experiment": False,
                "off_topic": True,
            }

    return {
        "topic": topic,
        "reply": parsed.get("reply") or _demo_reply(user_text, weakness, topic_hint)["reply"],
        "needs_experiment": bool(parsed.get("needs_experiment")) or weakness,
        "off_topic": False,
    }


def _call_claude(user_payload: dict, api_key: str) -> str | None:
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}],
        )
        return message.content[0].text if message.content else None
    except Exception:
        logger.exception("Fallo llamando a Claude")
        return None


def _extract_json(raw: str) -> dict | None:
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


def _demo_reply(user_text: str, weakness: bool, topic_hint: str | None) -> dict:
    topic = topic_hint or classify_topic_heuristic(user_text)
    if not topic:
        return {
            "topic": None,
            "reply": (
                "¡Hola! Soy Yachay. Por ahora te ayudo con: densidad/flotación, fotosíntesis, "
                "estados de la materia, electricidad básica y sistema digestivo. "
                "¿Sobre cuál es tu duda?"
            ),
            "needs_experiment": False,
            "off_topic": True,
        }

    meta = TOPICS[topic]
    label = topic_label(topic)
    reply = (
        f"**{label}** — Idea clave: lo explico simple.\n"
        f"{_mini_explain(topic)}\n\n"
        f"Ejemplo boliviano: {meta['example_bo']}\n\n"
        f"Chequeo: {_check_question(topic)}"
    )
    if weakness and meta.get("allows_experiment"):
        reply += "\n\nVeo que este tema se te complica. Te armo un mini-experimento casero."
    return {
        "topic": topic,
        "reply": reply,
        "needs_experiment": weakness and meta.get("allows_experiment", False),
        "off_topic": False,
    }


def _mini_explain(topic: str) -> str:
    return {
        "densidad_flotacion": "Un objeto flota si el líquido es más denso que él; si no, se hunde.",
        "fotosintesis": "Las plantas usan luz, agua y CO₂ para hacer su alimento y liberar oxígeno.",
        "estados_materia": "Sólido, líquido y gas son estados; cambian con la temperatura/energía.",
        "electricidad_basica": "La corriente eléctrica necesita un circuito cerrado para circular.",
        "sistema_digestivo": "El alimento se tritura y se absorbe desde la boca hasta el intestino.",
    }.get(topic, "Vamos paso a paso.")


def _check_question(topic: str) -> str:
    return {
        "densidad_flotacion": "¿Por qué un huevo puede flotar en agua con mucha sal?",
        "fotosintesis": "¿Qué le pasa a una planta si la dejas días sin luz?",
        "estados_materia": "¿Qué estado es el vapor de una olla hirviendo?",
        "electricidad_basica": "¿Qué pasa si abres el circuito de una linterna?",
        "sistema_digestivo": "¿En qué órgano se absorben la mayoría de nutrientes?",
    }.get(topic, "¿Me lo puedes explicar con tus palabras?")
