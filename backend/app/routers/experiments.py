from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Experiment, Student
from app.schemas import ExperimentOut

router = APIRouter(tags=["experiments"])


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
    return [
        ExperimentOut(
            id=e.id,
            student_id=e.student_id,
            student_code=s.code,
            student_name=s.display_name,
            topic=e.topic,
            title=e.title,
            materials=e.materials,
            steps=e.steps,
            explanation=e.explanation,
            created_at=e.created_at,
        )
        for e, s in rows
    ]
