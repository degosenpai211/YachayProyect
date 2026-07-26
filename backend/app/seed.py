import logging

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Experiment, Message, Student, Weakness
from app.services.agent import register_or_get_student

logger = logging.getLogger("yachay.seed")

# Prefijo que usa seed_demo_data en telegram_id (nunca un chat real de Telegram).
_DEMO_TELEGRAM_PREFIX = "tg_"


def clear_demo_seed_data(db: Session) -> int:
    """Borra alumnos/mensajes sembrados por DEMO_MODE (telegram_id tipo tg_...).

    No toca alumnos reales de Telegram (chat IDs numéricos / telegram:...).
    """
    demo_ids = list(
        db.scalars(
            select(Student.id).where(Student.telegram_id.startswith(_DEMO_TELEGRAM_PREFIX))
        ).all()
    )
    if not demo_ids:
        return 0

    db.execute(delete(Message).where(Message.student_id.in_(demo_ids)))
    db.execute(delete(Weakness).where(Weakness.student_id.in_(demo_ids)))
    db.execute(delete(Experiment).where(Experiment.student_id.in_(demo_ids)))
    db.execute(delete(Student).where(Student.id.in_(demo_ids)))
    db.commit()
    logger.info("DEMO_MODE=false: eliminados %s alumnos de seed de demo", len(demo_ids))
    return len(demo_ids)


def seed_demo_data(db: Session) -> None:
    """Carga datos de demo si la DB está vacía."""
    exists = db.scalar(select(Student).limit(1))
    if exists:
        return

    samples = [
        ("UEBOL-3A-01", "Ana Quispe", "UEBOL-3A"),
        ("UEBOL-3A-07", "Luis Mamani", "UEBOL-3A"),
        ("UEBOL-3A-12", "María Condori", "UEBOL-3A"),
        ("UEBOL-3B-03", "Diego Flores", "UEBOL-3B"),
    ]

    for code, name, _course in samples:
        register_or_get_student(db, code=code, telegram_id=f"tg_{code}", display_name=name)

    ana = db.scalar(select(Student).where(Student.code == "UEBOL-3A-01"))
    luis = db.scalar(select(Student).where(Student.code == "UEBOL-3A-07"))
    maria = db.scalar(select(Student).where(Student.code == "UEBOL-3A-12"))

    turns = [
        (ana, "student", "¿Por qué un huevo se hunde en el agua?", "densidad_flotacion", False),
        (ana, "assistant", "Porque el agua es menos densa que el huevo…", "densidad_flotacion", False),
        (ana, "student", "¿Y si le pongo sal al agua el huevo flota?", "densidad_flotacion", True),
        (luis, "student", "¿Qué es la fotosíntesis?", "fotosintesis", False),
        (luis, "assistant", "Las plantas hacen su alimento con luz…", "fotosintesis", False),
        (maria, "student", "¿Cómo funciona un circuito eléctrico?", "electricidad_basica", False),
        (maria, "student", "¿Por qué se apaga si abro el interruptor?", "electricidad_basica", True),
    ]

    for student, role, content, topic, weakness in turns:
        db.add(
            Message(
                student_id=student.id,
                role=role,
                content=content,
                topic=topic,
                is_weakness=weakness,
            )
        )

    db.add(
        Weakness(student_id=ana.id, topic="densidad_flotacion", hit_count=2, active=True)
    )
    db.add(
        Weakness(student_id=maria.id, topic="electricidad_basica", hit_count=2, active=True)
    )
    db.add(
        Experiment(
            student_id=ana.id,
            topic="densidad_flotacion",
            title="Huevo que flota con sal",
            materials="Vaso, agua, huevo, sal",
            steps="1) Huevo en agua. 2) Agregar sal. 3) Observar flotación.",
            explanation="El agua salada es más densa y sostiene al huevo.",
            status="pending",
            feedback="",
        )
    )
    db.commit()
