from functools import wraps
from typing import Any, Callable

import jwt
from flask import g, request
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.session import get_session
from app.models.user import User
from app.repositories.user_repository import UserRepository


def _decode_jwt(token: str) -> dict[str, Any]:
    settings = Settings()
    if not settings.clerk_jwt_public_key:
        raise ValueError("CLERK_JWT_PUBLIC_KEY is not configured")

    return jwt.decode(
        token,
        settings.clerk_jwt_public_key,
        algorithms=["RS256"],
        options={"verify_aud": False},
    )


def _get_or_create_user(session: Session, payload: dict[str, Any]) -> User:
    clerk_user_id = payload.get("sub")
    email = payload.get("email")
    if not clerk_user_id or not email:
        raise ValueError("Missing user info in Clerk token")

    repo = UserRepository(session)
    user = repo.get_by_clerk_id(clerk_user_id)
    if user:
        return user

    user = User(clerk_user_id=clerk_user_id, email=email)
    return repo.upsert(user)


def clerk_required(handler: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(handler)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return {"error": "Unauthorized"}, 401

        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = _decode_jwt(token)
        except Exception:
            return {"error": "Unauthorized"}, 401

        session = next(get_session())
        try:
            g.current_user = _get_or_create_user(session, payload)
        finally:
            session.close()

        return handler(*args, **kwargs)

    return wrapper
