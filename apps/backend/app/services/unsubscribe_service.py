from sqlalchemy.orm import Session

from app.models.email import Email
from app.repositories.email_repository import EmailRepository


class UnsubscribeService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.email_repo = EmailRepository(session)

    def unsubscribe(self, email_id: int, user_id: int) -> Email:
        email = self.email_repo.get_by_id(email_id, user_id)
        if email is None:
            raise ValueError("Email not found")

        # TODO: Implement Playwright flow that opens unsubscribe link.
        # NOTE: Must be triggered by explicit user action.
        email.unsubscribed = True
        self.session.add(email)
        self.session.commit()
        self.session.refresh(email)
        return email
