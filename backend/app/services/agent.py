import re
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Experiment, Message, Student, Weakness
from app.schemas import ChatProcessResult
from app.services.claude import generate_tutor_reply
from app.services.exa_svc import ground_bolivian_example
from app.topics import EXPERIMENT_TEMPLATES, TOPICS, topic_label

CODE_RE = re.compile(r"^[A-Za-z0-9]{2,}[-_][A-Za-z0-9]{1,}[-_][A-Za-z0-9]{1,}$")
WEAKNESS_THRESHOLD = 2
HISTORY_LIMIT = 6  # ~3 turnos (alumno+tutor)
DONE_RE = re.compile(
    r"^(experimento\s+)?(hecho|listo|terminé|termine|completé|complete)\b",
    re.IGNORECASE,
)


def parse_course_from_code(code: str) -> str:
    parts = re.split(r"[-_]", code.upper())
    if len(parts) >= 2:
        return f"{parts[0]}-{parts[1]}"
    return code.upper()


def normalize_code(raw: str) -> str:
    return raw.strip().upper().replace("_", "-")


def extract_student_code(text: str) -> str | None:
    """Acepta código suelto, /start CODE y deep links de Telegram."""
    text = (text or "").strip()
    if not text:
        return None

    lowered = text.lower()
    if lowered.startswith("/start"):
        # /start UEBOL-3A-12  |  /start@Bot UEBOL_3A_12  |  /startUEBOL-3A-12
        rest = text[6:].lstrip()
        if rest.startswith("@"):
            parts = rest.split(maxsplit=1)
            rest = parts[1] if len(parts) > 1 else ""
        token = (rest.split()[0] if rest else "").strip()
        if not token:
            return None
        code = normalize_code(token)
        return code if CODE_RE.match(code) else None

    # Primer token o texto completo
    first = normalize_code(text.split()[0])
    if CODE_RE.match(first):
        return first
    whole = normalize_code(text)
    if CODE_RE.match(whole):
        return whole
    return None


def find_student_by_sender(db: Session, sender: str) -> Student | None:
    return db.scalar(select(Student).where(Student.telegram_id == sender))


def register_or_get_student(
    db: Session,
    code: str,
    telegram_id: str | None = None,
    display_name: str | None = None,
) -> Student:
    normalized = normalize_code(code)
    student = db.scalar(select(Student).where(Student.code == normalized))
    if student:
        if telegram_id and student.telegram_id != telegram_id:
            student.telegram_id = telegram_id
        if display_name and not student.display_name:
            student.display_name = display_name
        db.commit()
        db.refresh(student)
        return student

    student = Student(
        code=normalized,
        course=parse_course_from_code(normalized),
        telegram_id=telegram_id,
        display_name=display_name or f"Estudiante {normalized.split('-')[-1]}",
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def _count_topic_hits(db: Session, student_id: int, topic: str) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Message)
            .where(
                Message.student_id == student_id,
                Message.role == "student",
                Message.topic == topic,
            )
        )
        or 0
    )


def _upsert_weakness(db: Session, student_id: int, topic: str, hit_count: int) -> Weakness:
    weakness = db.scalar(
        select(Weakness).where(Weakness.student_id == student_id, Weakness.topic == topic)
    )
    if weakness:
        weakness.hit_count = hit_count
        weakness.active = True
        weakness.updated_at = datetime.utcnow()
    else:
        weakness = Weakness(
            student_id=student_id,
            topic=topic,
            hit_count=hit_count,
            active=True,
        )
        db.add(weakness)
    db.commit()
    db.refresh(weakness)
    return weakness


def _create_experiment(db: Session, student_id: int, topic: str) -> Experiment | None:
    template = EXPERIMENT_TEMPLATES.get(topic)
    if not template:
        return None
    existing = db.scalar(
        select(Experiment).where(Experiment.student_id == student_id, Experiment.topic == topic)
    )
    if existing:
        return existing

    exp = Experiment(
        student_id=student_id,
        topic=topic,
        title=template["title"],
        materials=template["materials"],
        steps=template["steps"],
        explanation=template["explanation"],
        status="pending",
        feedback="",
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


def _format_experiment(exp: Experiment) -> str:
    return (
        f"\n\n🧪 Mini-experimento: {exp.title}\n"
        f"Materiales: {exp.materials}\n"
        f"Pasos:\n{exp.steps}\n"
        f"Por qué funciona: {exp.explanation}\n"
        f"Cuando lo hagas, escribe: experimento hecho (y un comentario si quieres)."
    )


def _recent_history(db: Session, student_id: int) -> list[dict]:
    rows = db.scalars(
        select(Message)
        .where(Message.student_id == student_id)
        .order_by(Message.id.desc())
        .limit(HISTORY_LIMIT)
    ).all()
    rows = list(reversed(rows))
    return [{"role": m.role, "content": m.content[:400]} for m in rows]


def _try_mark_experiment_done(db: Session, student: Student, text: str) -> str | None:
    match = DONE_RE.match(text.strip())
    if not match:
        return None
    exp = db.scalar(
        select(Experiment)
        .where(Experiment.student_id == student.id, Experiment.status == "pending")
        .order_by(Experiment.created_at.desc())
    )
    if not exp:
        return (
            "No tengo un experimento pendiente tuyo. Pregúntame de un tema y, "
            "si hace falta, te armo uno."
        )
    feedback = text.strip()[match.end() :].lstrip(" :.-").strip()
    exp.status = "done"
    exp.feedback = feedback
    db.commit()
    extra = f" Comentario guardado: “{feedback}”." if feedback else ""
    return (
        f"¡Genial! Marqué como hecho: {exp.title} ({topic_label(exp.topic)}).{extra}\n"
        "Si quieres, cuéntame qué observaste o pregunta otra duda de ciencias."
    )


async def process_student_message(
    db: Session,
    sender: str,
    text: str,
) -> ChatProcessResult:
    text = (text or "").strip()
    if not text:
        return ChatProcessResult(
            reply="No recibí texto. Escríbeme tu duda o manda audio otra vez.",
            needs_code=False,
        )

    student = find_student_by_sender(db, sender)

    # Primer mensaje / registro: código o /start CODE
    if not student:
        code = extract_student_code(text)
        if code:
            student = register_or_get_student(db, code=code, telegram_id=sender)
            return ChatProcessResult(
                reply=(
                    f"¡Listo, {student.display_name}! Código {student.code} registrado "
                    f"(curso {student.course}).\n"
                    "Pregúntame de ciencias: densidad, fotosíntesis, materia, electricidad o digestivo."
                ),
                student_code=student.code,
                needs_code=False,
            )
        return ChatProcessResult(
            reply=(
                "¡Hola! Soy Yachay 👋\n"
                "Para empezar, escribe tu código de estudiante (ej: UEBOL-3A-12)."
            ),
            needs_code=True,
        )

    # Re-vincular si manda /start CODE o solo el código
    code = extract_student_code(text)
    tokens = text.split()
    only_code = bool(code) and len(tokens) == 1 and not text.lower().startswith("/start")
    if code and (text.lower().startswith("/start") or only_code):
        student = register_or_get_student(db, code=code, telegram_id=sender)
        return ChatProcessResult(
            reply=(
                f"Código {student.code} listo (curso {student.course}). "
                "¿Qué duda de ciencias tienes?"
            ),
            student_code=student.code,
            needs_code=False,
        )

    # Marcar experimento hecho (sin gastar LLM)
    done_reply = _try_mark_experiment_done(db, student, text)
    if done_reply:
        db.add(
            Message(
                student_id=student.id,
                role="student",
                content=text,
                topic=None,
                is_weakness=False,
            )
        )
        db.add(
            Message(
                student_id=student.id,
                role="assistant",
                content=done_reply,
                topic=None,
                is_weakness=False,
            )
        )
        db.commit()
        return ChatProcessResult(
            reply=done_reply,
            student_code=student.code,
            needs_code=False,
        )

    history = _recent_history(db, student.id)

    db.add(
        Message(
            student_id=student.id,
            role="student",
            content=text,
            topic=None,
            is_weakness=False,
        )
    )
    db.commit()

    tutor = await generate_tutor_reply(
        text,
        weakness=False,
        topic_hint=None,
        history=history,
    )
    topic = tutor.get("topic")
    off_topic = bool(tutor.get("off_topic"))

    is_weakness = False
    experiment_created = False
    reply = tutor["reply"]

    if topic and not off_topic:
        last_msg = db.scalar(
            select(Message)
            .where(Message.student_id == student.id, Message.role == "student")
            .order_by(Message.id.desc())
        )
        if last_msg and last_msg.topic != topic:
            last_msg.topic = topic
            db.commit()
        hit_count = _count_topic_hits(db, student.id, topic)

        is_weakness = hit_count >= WEAKNESS_THRESHOLD
        if last_msg:
            last_msg.is_weakness = is_weakness
            db.commit()

        if is_weakness:
            _upsert_weakness(db, student.id, topic, hit_count)
            if TOPICS.get(topic, {}).get("allows_experiment"):
                reply += "\n\nVeo que este tema se te complica. Te armo un mini-experimento casero."
                exp = _create_experiment(db, student.id, topic)
                if exp:
                    experiment_created = True
                    reply += _format_experiment(exp)
            else:
                reply += "\n\nVeo que este tema se te complica un poco. Sigamos practicando con más preguntas."

        grounded = await ground_bolivian_example(topic_label(topic), text)
        if grounded:
            reply += f"\n\n📎 Dato extra: {grounded}"

    db.add(
        Message(
            student_id=student.id,
            role="assistant",
            content=reply,
            topic=topic,
            is_weakness=is_weakness,
        )
    )
    db.commit()

    return ChatProcessResult(
        reply=reply,
        topic=topic,
        is_weakness=is_weakness,
        experiment_created=experiment_created,
        student_code=student.code,
        needs_code=False,
    )
