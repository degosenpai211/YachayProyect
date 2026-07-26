from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Experiment, Message, Student, Weakness
from app.schemas import DashboardStats, TopicWeaknessAgg
from app.topics import topic_label

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    students = db.scalar(select(func.count()).select_from(Student)) or 0
    messages = db.scalar(select(func.count()).select_from(Message)) or 0
    active_weaknesses = (
        db.scalar(select(func.count()).select_from(Weakness).where(Weakness.active.is_(True))) or 0
    )
    experiments = db.scalar(select(func.count()).select_from(Experiment)) or 0

    rows = db.execute(
        select(
            Weakness.topic,
            func.count(func.distinct(Weakness.student_id)).label("student_count"),
            func.sum(Weakness.hit_count).label("total_hits"),
        )
        .where(Weakness.active.is_(True))
        .group_by(Weakness.topic)
        .order_by(func.sum(Weakness.hit_count).desc())
    ).all()

    topics = [
        TopicWeaknessAgg(
            topic=r.topic,
            topic_label=topic_label(r.topic),
            student_count=r.student_count or 0,
            total_hits=int(r.total_hits or 0),
        )
        for r in rows
    ]

    return DashboardStats(
        students=students,
        messages=messages,
        active_weaknesses=active_weaknesses,
        experiments=experiments,
        topics=topics,
    )
