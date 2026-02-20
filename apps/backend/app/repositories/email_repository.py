from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.email import Email, ImportanceEnum


class EmailRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_user(self, user_id: int) -> list[Email]:
        return self.session.scalars(select(Email).where(Email.user_id == user_id)).all()

    def list_important(self, user_id: int) -> list[Email]:
        stmt = select(Email).where(
            Email.user_id == user_id,
            Email.importance == ImportanceEnum.HIGH,
        )
        return self.session.scalars(stmt).all()

    def count_by_user(self, user_id: int) -> int:
        stmt = select(func.count(Email.id)).where(Email.user_id == user_id)
        return int(self.session.scalar(stmt) or 0)

    def get_by_id(self, email_id: int, user_id: int) -> Email | None:
        stmt = select(Email).where(Email.id == email_id, Email.user_id == user_id)
        return self.session.scalars(stmt).first()

    def get_by_gmail_id(self, user_id: int, gmail_message_id: str) -> Email | None:
        stmt = select(Email).where(
            Email.user_id == user_id,
            Email.gmail_message_id == gmail_message_id,
        )
        return self.session.scalars(stmt).first()

    def upsert(self, email: Email) -> Email:
        existing = self.get_by_gmail_id(email.user_id, email.gmail_message_id)
        if existing:
            existing.subject = email.subject
            existing.sender = email.sender
            existing.snippet = email.snippet
            existing.body = email.body
            existing.importance = email.importance
            existing.is_spam = email.is_spam
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing

        self.session.add(email)
        self.session.commit()
        self.session.refresh(email)
        return email
