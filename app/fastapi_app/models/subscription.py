"""Subscription model — SQLAlchemy 2.0 declarative style."""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.fastapi_app.db.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    merchant_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    frequency: Mapped[str] = mapped_column(String(30), nullable=False, default="monthly")
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_detected: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_expected: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    detection_confidence: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", back_populates="subscriptions")

    @property
    def yearly_cost(self) -> float:
        multipliers = {"daily": 365, "weekly": 52, "monthly": 12, "quarterly": 4, "yearly": 1}
        return float(self.amount) * multipliers.get(self.frequency, 12)

    def __repr__(self) -> str:
        return f"<Subscription id={self.id} name={self.name!r} amount={self.amount}/{self.frequency}>"
