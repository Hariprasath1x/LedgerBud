"""Wallet model for user-owned balances."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.fastapi_app.db.base import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    wallet_name: Mapped[str] = mapped_column(String(120), nullable=False)
    wallet_type: Mapped[str] = mapped_column(String(30), nullable=False)
    balance: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User", back_populates="wallets")
    transactions = relationship("Transaction", back_populates="wallet", cascade="all, delete-orphan")
    import_jobs = relationship("ImportJob", back_populates="wallet")

    def __repr__(self) -> str:
        return f"<Wallet id={self.id} name={self.wallet_name!r}>"

