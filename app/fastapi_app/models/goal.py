"""Goal model — SQLAlchemy 2.0 declarative style."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.fastapi_app.db.base import Base


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    current_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")  # active, completed, paused
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User", back_populates="goals")

    @property
    def progress_percentage(self) -> float:
        if self.target_amount and float(self.target_amount) > 0:
            return min(100.0, (float(self.current_amount) / float(self.target_amount)) * 100)
        return 0.0

    @property
    def remaining_amount(self) -> float:
        return max(0.0, float(self.target_amount) - float(self.current_amount))

    def __repr__(self) -> str:
        return f"<Goal id={self.id} name={self.name!r} progress={self.progress_percentage:.1f}%>"
