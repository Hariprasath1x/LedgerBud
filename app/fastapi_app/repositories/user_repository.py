"""User persistence operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.fastapi_app.models.user import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email.lower())
        return self.session.scalar(statement)

    def create(self, *, full_name: str, email: str, password_hash: str) -> User:
        user = User(full_name=full_name.strip(), email=email.lower().strip(), password_hash=password_hash)
        self.session.add(user)
        self.session.flush()
        return user
