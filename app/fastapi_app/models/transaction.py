"""Transaction model for wallet activity."""

from datetime import datetime, date

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.fastapi_app.db.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True)
    merchant_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    # Transfer tracking — nullable for backward-compat with existing rows
    is_transfer: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False, server_default="0")
    transfer_pair_id: Mapped[int | None] = mapped_column(
        ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    user = relationship("User", back_populates="transactions")
    wallet = relationship("Wallet", back_populates="transactions")
    transfer_pair = relationship("Transaction", remote_side="Transaction.id", foreign_keys=[transfer_pair_id])

    def __repr__(self) -> str:
        return f"<Transaction id={self.id} amount={self.amount}>"
