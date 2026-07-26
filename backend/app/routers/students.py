from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Experiment, Message, Student, Weakness
from app.schemas import StudentDetail, StudentOut, StudentRegister
from app.services.agent import register_or_get_student

router = APIRouter(prefix="/students", tags=["students"])


@router.post("/register", response_model=StudentOut)
def register_student(body: StudentRegister, db: Session = Depends(get_db)):
    student = register_or_get_student(
        db,
        code=body.code,
        telegram_id=body.telegram_id,
        display_name=body.display_name,
    )
    return _to_out(db, student)


@router.get("", response_model=list[StudentOut])
def list_students(course: str | None = None, db: Session = Depends(get_db)):
    q = select(Student).order_by(Student.code)
    if course:
        q = q.where(Student.course == course.upper())
    students = db.scalars(q).all()
    return [_to_out(db, s) for s in students]


@router.get("/{code}", response_model=StudentDetail)
def get_student(code: str, db: Session = Depends(get_db)):
    student = db.scalar(select(Student).where(Student.code == code.upper()))
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    base = _to_out(db, student)
    messages = db.scalars(
        select(Message).where(Message.student_id == student.id).order_by(Message.created_at.desc()).limit(50)
    ).all()
    weaknesses = db.scalars(
        select(Weakness).where(Weakness.student_id == student.id, Weakness.active.is_(True))
    ).all()
    experiments = db.scalars(
        select(Experiment).where(Experiment.student_id == student.id).order_by(Experiment.created_at.desc())
    ).all()

    return StudentDetail(
        **base.model_dump(),
        messages=list(reversed(messages)),
        weaknesses=[
            {
                "id": w.id,
                "student_id": w.student_id,
                "student_code": student.code,
                "student_name": student.display_name,
                "topic": w.topic,
                "hit_count": w.hit_count,
                "active": w.active,
                "updated_at": w.updated_at,
            }
            for w in weaknesses
        ],
        experiments=[
            {
                "id": e.id,
                "student_id": e.student_id,
                "student_code": student.code,
                "student_name": student.display_name,
                "topic": e.topic,
                "title": e.title,
                "materials": e.materials,
                "steps": e.steps,
                "explanation": e.explanation,
                "status": getattr(e, "status", None) or "pending",
                "feedback": getattr(e, "feedback", None) or "",
                "created_at": e.created_at,
            }
            for e in experiments
        ],
    )


def _to_out(db: Session, student: Student) -> StudentOut:
    msg_count = db.scalar(
        select(func.count()).select_from(Message).where(Message.student_id == student.id)
    ) or 0
    weak_count = db.scalar(
        select(func.count())
        .select_from(Weakness)
        .where(Weakness.student_id == student.id, Weakness.active.is_(True))
    ) or 0
    return StudentOut(
        id=student.id,
        code=student.code,
        display_name=student.display_name,
        course=student.course,
        telegram_id=student.telegram_id,
        created_at=student.created_at,
        weakness_count=weak_count,
        message_count=msg_count,
    )
