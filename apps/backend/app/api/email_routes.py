from flask import Blueprint, g, request

from app.auth.clerk_middleware import clerk_required
from app.db.session import get_session
from app.llm.gemini_client import GeminiClient
from app.schemas.email import EmailCount, EmailRead, EmailReplyCreate, EmailReplySend
from app.services.email_service import EmailService
from app.services.reply_service import ReplyService
from app.services.sync_service import sync_emails_for_user
from app.services.unsubscribe_service import UnsubscribeService

email_bp = Blueprint("emails", __name__)


@email_bp.get("")
@clerk_required
def list_emails():
    session = next(get_session())
    try:
        service = EmailService(session)
        emails = service.list_emails(g.current_user.id)
        return [EmailRead.model_validate(email).model_dump() for email in emails]
    finally:
        session.close()


@email_bp.get("/count")
@clerk_required
def email_count():
    session = next(get_session())
    try:
        service = EmailService(session)
        total = service.count_emails(g.current_user.id)
        return EmailCount(total=total).model_dump()
    finally:
        session.close()


@email_bp.get("/important")
@clerk_required
def important_emails():
    session = next(get_session())
    try:
        service = EmailService(session)
        emails = service.list_important(g.current_user.id)
        return [EmailRead.model_validate(email).model_dump() for email in emails]
    finally:
        session.close()


@email_bp.post("/reply")
@clerk_required
def generate_reply():
    payload = EmailReplyCreate(**request.get_json(force=True))
    session = next(get_session())
    try:
        llm = GeminiClient()
        service = ReplyService(session, llm)
        try:
            reply = service.generate_reply(payload.email_id, g.current_user.id)
        except ValueError:
            return {"error": "Email not found"}, 404
        return {
            "id": reply.id,
            "email_id": reply.email_id,
            "reply_text": reply.reply_text,
            "status": reply.status,
        }
    finally:
        session.close()


@email_bp.post("/send")
@clerk_required
def send_reply():
    payload = EmailReplySend(**request.get_json(force=True))
    session = next(get_session())
    try:
        llm = GeminiClient()
        service = ReplyService(session, llm)
        try:
            reply = service.send_reply(payload.email_id, g.current_user.id, payload.reply_text)
        except ValueError:
            return {"error": "Email not found"}, 404
        return {
            "id": reply.id,
            "email_id": reply.email_id,
            "reply_text": reply.reply_text,
            "status": reply.status,
            "sent_at": reply.sent_at.isoformat() if reply.sent_at else None,
        }
    finally:
        session.close()


@email_bp.post("/sync")
@clerk_required
def sync_emails():
    session = next(get_session())
    try:
        count = sync_emails_for_user(session, g.current_user)
        return {"synced": count}
    finally:
        session.close()


@email_bp.post("/unsubscribe")
@clerk_required
def unsubscribe():
    payload = EmailReplyCreate(**request.get_json(force=True))
    session = next(get_session())
    try:
        service = UnsubscribeService(session)
        try:
            email = service.unsubscribe(payload.email_id, g.current_user.id)
        except ValueError:
            return {"error": "Email not found"}, 404
        return {"email_id": email.id, "unsubscribed": email.unsubscribed}
    finally:
        session.close()
