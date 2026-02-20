from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_clerk_id(self, clerk_user_id: str) -> User | None:
        stmt = select(User).where(User.clerk_user_id == clerk_user_id)
        return self.session.scalars(stmt).first()

    def upsert(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
