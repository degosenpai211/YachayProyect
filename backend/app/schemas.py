from datetime import datetime

from pydantic import BaseModel, Field


class StudentRegister(BaseModel):
    code: str = Field(min_length=3, max_length=64)
    telegram_id: str | None = None
    display_name: str | None = None


class StudentOut(BaseModel):
    id: int
    code: str
    display_name: str
    course: str
    telegram_id: str | None
    created_at: datetime
    weakness_count: int = 0
    message_count: int = 0

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    topic: str | None
    is_weakness: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class StudentDetail(StudentOut):
    messages: list[MessageOut] = []
    weaknesses: list["WeaknessOut"] = []
    experiments: list["ExperimentOut"] = []


class WeaknessOut(BaseModel):
    id: int
    student_id: int
    student_code: str = ""
    student_name: str = ""
    topic: str
    hit_count: int
    active: bool
    updated_at: datetime

    model_config = {"from_attributes": True}


class TopicWeaknessAgg(BaseModel):
    topic: str
    topic_label: str
    student_count: int
    total_hits: int


class ExperimentOut(BaseModel):
    id: int
    student_id: int
    student_code: str = ""
    student_name: str = ""
    topic: str
    title: str
    materials: str
    steps: str
    explanation: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ZavuWebhookIn(BaseModel):
    """Payload flexible: acepta formas comunes de Zavu/Telegram-like."""

    message: str | None = None
    text: str | None = None
    body: str | None = None
    from_: str | None = Field(default=None, alias="from")
    sender: str | None = None
    telegram_id: str | None = None
    user_id: str | None = None
    audio_url: str | None = None
    media_url: str | None = None
    channel: str | None = None

    model_config = {"populate_by_name": True}

    def resolved_text(self) -> str:
        return (self.message or self.text or self.body or "").strip()

    def resolved_sender(self) -> str:
        return (self.telegram_id or self.user_id or self.from_ or self.sender or "anon").strip()


class ChatProcessResult(BaseModel):
    reply: str
    topic: str | None = None
    is_weakness: bool = False
    experiment_created: bool = False
    student_code: str | None = None
    needs_code: bool = False


class DashboardStats(BaseModel):
    students: int
    messages: int
    active_weaknesses: int
    experiments: int
    topics: list[TopicWeaknessAgg]
