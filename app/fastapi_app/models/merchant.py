"""Merchant model for Financial Intelligence Pipeline."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.fastapi_app.db.base import Base


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    unique_identifier: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    preferred_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, default="Unknown")
    
    user_confirmation_status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    
    recognition_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    total_transactions: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    total_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0.0, server_default="0.0")

    user = relationship("User", back_populates="merchants")
    transactions = relationship("Transaction", back_populates="merchant")

    def __repr__(self) -> str:
        return f"<Merchant id={self.id} display_name={self.display_name!r}>"
