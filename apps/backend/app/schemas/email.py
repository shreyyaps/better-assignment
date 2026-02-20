from datetime import datetime
from pydantic import BaseModel

from app.models.email import ImportanceEnum


class EmailBase(BaseModel):
    subject: str | None
    sender: str | None
    snippet: str | None
    body: str | None
    importance: ImportanceEnum
    is_spam: bool
    unsubscribed: bool


class EmailRead(EmailBase):
    id: int
    gmail_message_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class EmailReplyCreate(BaseModel):
    email_id: int


class EmailReplySend(BaseModel):
    email_id: int
    reply_text: str


class EmailCount(BaseModel):
    total: int
