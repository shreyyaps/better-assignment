from sqlalchemy.orm import Session

from app.models.email import Email
from app.models.user import User
from app.orchestration.email_graph import run_email_graph
from app.repositories.email_repository import EmailRepository
from sqlalchemy import select

from app.repositories.user_repository import UserRepository


def sync_emails_for_user(session: Session, user: User) -> int:
    """Fetch, classify, and store emails for a single user.

    Returns number of emails stored.
    """
    graph_output = run_email_graph(user)
    repo = EmailRepository(session)

    stored = 0
    for item in graph_output.get("emails", []):
        email = Email(
            user_id=user.id,
            gmail_message_id=item["gmail_message_id"],
            subject=item.get("subject"),
            sender=item.get("sender"),
            snippet=item.get("snippet"),
            body=item.get("body"),
            importance=item["importance"],
            is_spam=item.get("is_spam", False),
            unsubscribed=False,
        )
        repo.upsert(email)
        stored += 1

    return stored


def sync_emails_for_all_users(session: Session) -> int:
    """Sync emails for all users.

    TODO: move to a queue for large user counts.
    """
    _ = UserRepository(session)
    users = session.scalars(select(User)).all()

    total = 0
    for user in users:
        total += sync_emails_for_user(session, user)

    return total
