from sqlalchemy.orm import Session

from app.models.email import Email
from app.repositories.email_repository import EmailRepository


class EmailService:
    def __init__(self, session: Session) -> None:
        self.repo = EmailRepository(session)

    def list_emails(self, user_id: int) -> list[Email]:
        return self.repo.list_by_user(user_id)

    def list_important(self, user_id: int) -> list[Email]:
        return self.repo.list_important(user_id)

    def count_emails(self, user_id: int) -> int:
        return self.repo.count_by_user(user_id)

    def get_email(self, email_id: int, user_id: int) -> Email | None:
        return self.repo.get_by_id(email_id, user_id)
