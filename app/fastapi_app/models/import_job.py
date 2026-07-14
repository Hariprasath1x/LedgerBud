"""ImportJob model — SQLAlchemy 2.0 declarative style."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.fastapi_app.db.base import Base


class ImportJob(Base):
    __tablename__ = "import_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id", ondelete="SET NULL"), nullable=True, index=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    institution_detected: Mapped[str | None] = mapped_column(String(100), nullable=True)
    account_number_detected: Mapped[str | None] = mapped_column(String(50), nullable=True)
    statement_period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    statement_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    imported_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    preview_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="import_jobs")
    wallet = relationship("Wallet", back_populates="import_jobs")

    def __repr__(self) -> str:
        return f"<ImportJob id={self.id} file={self.original_filename!r} status={self.status!r}>"
