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


def parse_course_from_code(code: str) -> str:
    parts = re.split(r"[-_]", code.upper())
    if len(parts) >= 2:
        return f"{parts[0]}-{parts[1]}"
    return code.upper()


def find_student_by_sender(db: Session, sender: str) -> Student | None:
    return db.scalar(select(Student).where(Student.telegram_id == sender))


def register_or_get_student(
    db: Session,
    code: str,
    telegram_id: str | None = None,
    display_name: str | None = None,
) -> Student:
    normalized = code.strip().upper()
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
    # Evitar spam: un experimento del mismo tema por estudiante
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
        f"Por qué funciona: {exp.explanation}"
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

    # Primer mensaje: código de estudiante
    if not student:
        maybe_code = text.split()[0].strip().upper()
        if CODE_RE.match(maybe_code) or CODE_RE.match(text.upper()):
            code = maybe_code if CODE_RE.match(maybe_code) else text.upper()
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

    # Turno de tutoría
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

    # Contar hits tentativos después de clasificar
    tutor = await generate_tutor_reply(text, weakness=False, topic_hint=None)
    topic = tutor.get("topic")

    is_weakness = False
    experiment_created = False
    reply = tutor["reply"]

    if topic:
        # Actualizar último mensaje del estudiante con topic
        last_msg = db.scalar(
            select(Message)
            .where(Message.student_id == student.id, Message.role == "student")
            .order_by(Message.id.desc())
        )
        hit_count = _count_topic_hits(db, student.id, topic)
        # el mensaje actual aún puede no tener topic; forzar conteo +1 si no estaba
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
            # Regenerar respuesta consciente de debilidad (demo/heurística ya lo contempla)
            tutor = await generate_tutor_reply(text, weakness=True, topic_hint=topic)
            reply = tutor["reply"]
            topic = tutor.get("topic") or topic

            if TOPICS.get(topic, {}).get("allows_experiment"):
                exp = _create_experiment(db, student.id, topic)
                if exp:
                    experiment_created = True
                    reply += _format_experiment(exp)

        # Grounding opcional (no bloquea)
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
