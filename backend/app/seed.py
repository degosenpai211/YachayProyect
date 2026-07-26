from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Experiment, Message, Student, Weakness
from app.services.agent import register_or_get_student


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
        )
    )
    db.commit()
