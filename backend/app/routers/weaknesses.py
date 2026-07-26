from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Student, Weakness
from app.schemas import TopicWeaknessAgg, WeaknessOut
from app.topics import topic_label

router = APIRouter(tags=["topic-weakness"])


@router.get("/topic-weakness", response_model=list[TopicWeaknessAgg])
def topic_weakness_agg(course: str | None = None, db: Session = Depends(get_db)):
    q = (
        select(
            Weakness.topic,
            func.count(func.distinct(Weakness.student_id)).label("student_count"),
            func.sum(Weakness.hit_count).label("total_hits"),
        )
        .where(Weakness.active.is_(True))
        .group_by(Weakness.topic)
        .order_by(func.sum(Weakness.hit_count).desc())
    )
    if course:
        q = q.join(Student, Student.id == Weakness.student_id).where(
            Student.course == course.upper()
        )

    rows = db.execute(q).all()
    return [
        TopicWeaknessAgg(
            topic=row.topic,
            topic_label=topic_label(row.topic),
            student_count=row.student_count or 0,
            total_hits=int(row.total_hits or 0),
        )
        for row in rows
    ]


@router.get("/weaknesses", response_model=list[WeaknessOut])
def list_weaknesses(course: str | None = None, db: Session = Depends(get_db)):
    q = (
        select(Weakness, Student)
        .join(Student, Student.id == Weakness.student_id)
        .where(Weakness.active.is_(True))
        .order_by(Weakness.updated_at.desc())
    )
    if course:
        q = q.where(Student.course == course.upper())

    rows = db.execute(q).all()
    return [
        WeaknessOut(
            id=w.id,
            student_id=w.student_id,
            student_code=s.code,
            student_name=s.display_name,
            topic=w.topic,
            hit_count=w.hit_count,
            active=w.active,
            updated_at=w.updated_at,
        )
        for w, s in rows
    ]
