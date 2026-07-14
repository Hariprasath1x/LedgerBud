"""Net Worth models — items and historical snapshots.

Items are explicit assets and liabilities entered by the user.
Snapshots record totals at a point in time for trend charting.
"""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.fastapi_app.db.base import Base


ASSET_CATEGORIES = [
    "Cash & Savings",
    "Fixed Deposit",
    "Stocks & Equity",
    "Mutual Funds",
    "Real Estate",
    "Gold & Commodities",
    "Provident Fund",
    "Other Asset",
]

LIABILITY_CATEGORIES = [
    "Home Loan",
    "Car Loan",
    "Personal Loan",
    "Credit Card Debt",
    "Education Loan",
    "Other Liability",
]


class NetWorthItem(Base):
    __tablename__ = "net_worth_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "asset" or "liability"
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User", back_populates="net_worth_items")

    def __repr__(self) -> str:
        return f"<NetWorthItem id={self.id} name={self.name!r} type={self.item_type}>"


class NetWorthSnapshot(Base):
    __tablename__ = "net_worth_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    total_assets: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    total_liabilities: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    net_worth: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", back_populates="net_worth_snapshots")

    def __repr__(self) -> str:
        return f"<NetWorthSnapshot id={self.id} date={self.snapshot_date} nw={self.net_worth}>"
