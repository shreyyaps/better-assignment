from datetime import datetime

from sqlalchemy.orm import Session

from app.llm.gemini_client import GeminiClient
from app.models.email_reply import EmailReply
from app.repositories.email_repository import EmailRepository


class ReplyService:
    def __init__(self, session: Session, llm: GeminiClient) -> None:
        self.session = session
        self.llm = llm
        self.email_repo = EmailRepository(session)

    def generate_reply(self, email_id: int, user_id: int) -> EmailReply:
        email = self.email_repo.get_by_id(email_id, user_id)
        if email is None:
            raise ValueError("Email not found")

        draft = self.llm.generate_reply(email.body or "")
        reply = EmailReply(email_id=email.id, reply_text=draft, status="draft")
        self.session.add(reply)
        self.session.commit()
        self.session.refresh(reply)
        return reply

    def send_reply(self, email_id: int, user_id: int, reply_text: str) -> EmailReply:
        email = self.email_repo.get_by_id(email_id, user_id)
        if email is None:
            raise ValueError("Email not found")

        reply = EmailReply(
            email_id=email.id,
            reply_text=reply_text,
            status="sent",
            sent_at=datetime.utcnow(),
        )
        self.session.add(reply)
        self.session.commit()
        self.session.refresh(reply)

        # TODO: integrate Gmail send API.
        return reply
