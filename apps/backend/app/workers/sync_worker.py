from app.db.session import get_session
from app.services.sync_service import sync_emails_for_all_users


def run_polling_sync() -> None:
    """Run a polling sync across all users.

    TODO: Use distributed locks to avoid multi-worker duplication.
    """
    session = next(get_session())
    try:
        sync_emails_for_all_users(session)
    finally:
        session.close()
