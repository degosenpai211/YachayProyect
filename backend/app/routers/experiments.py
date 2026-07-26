from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Experiment, Student
from app.schemas import ExperimentOut, ExperimentUpdate

router = APIRouter(tags=["experiments"])


def _to_out(e: Experiment, s: Student) -> ExperimentOut:
    return ExperimentOut(
        id=e.id,
        student_id=e.student_id,
        student_code=s.code,
        student_name=s.display_name,
        topic=e.topic,
        title=e.title,
        materials=e.materials,
        steps=e.steps,
        explanation=e.explanation,
        status=getattr(e, "status", None) or "pending",
        feedback=getattr(e, "feedback", None) or "",
        created_at=e.created_at,
    )


@router.get("/experiments", response_model=list[ExperimentOut])
def list_experiments(course: str | None = None, db: Session = Depends(get_db)):
    q = (
        select(Experiment, Student)
        .join(Student, Student.id == Experiment.student_id)
        .order_by(Experiment.created_at.desc())
    )
    if course:
        q = q.where(Student.course == course.upper())

    rows = db.execute(q).all()
    return [_to_out(e, s) for e, s in rows]


@router.patch("/experiments/{experiment_id}", response_model=ExperimentOut)
def update_experiment(
    experiment_id: int,
    body: ExperimentUpdate,
    db: Session = Depends(get_db),
):
    row = db.execute(
        select(Experiment, Student)
        .join(Student, Student.id == Experiment.student_id)
        .where(Experiment.id == experiment_id)
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Experimento no encontrado")
    exp, student = row
    if body.status is not None:
        status = body.status.strip().lower()
        if status not in {"pending", "done"}:
            raise HTTPException(status_code=400, detail="status debe ser pending o done")
        exp.status = status
    if body.feedback is not None:
        exp.feedback = body.feedback.strip()
    db.commit()
    db.refresh(exp)
    return _to_out(exp, student)
