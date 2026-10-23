"""Declarative SQLAlchemy base for the FastAPI backend."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
