"""FIRE Analysis model — stores historical FIRE calculation snapshots."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.fastapi_app.db.base import Base


class FireAnalysis(Base):
    __tablename__ = "fire_analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ── User-configurable inputs ──────────────────────────────────────────────
    current_age: Mapped[int] = mapped_column(Integer, nullable=False, default=25)
    retirement_target_age: Mapped[int] = mapped_column(Integer, nullable=False, default=45)
    investment_return: Mapped[float] = mapped_column(Float, nullable=False, default=12.0)
    inflation_rate: Mapped[float] = mapped_column(Float, nullable=False, default=6.0)
    lifestyle: Mapped[str] = mapped_column(String(50), nullable=False, default="Moderate")

    # ── Auto-calculated financial inputs ─────────────────────────────────────
    current_net_worth: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    annual_income: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    annual_expenses: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    annual_savings: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    savings_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # ── FIRE Outputs ──────────────────────────────────────────────────────────
    fire_target_corpus: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fire_progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fire_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    estimated_fire_age: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    years_remaining: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    required_monthly_investment: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # ── JSON blobs ────────────────────────────────────────────────────────────
    # wealth_projection: list of {year, nominal, real}
    wealth_projection: Mapped[dict] = mapped_column(JSON, nullable=True, default=None)
    # scenarios: list of {name, return_rate, corpus, fire_age, monthly_investment}
    scenarios: Mapped[dict] = mapped_column(JSON, nullable=True, default=None)
    # strengths / weaknesses: list of strings
    strengths: Mapped[dict] = mapped_column(JSON, nullable=True, default=None)
    weaknesses: Mapped[dict] = mapped_column(JSON, nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user = relationship("User", back_populates="fire_analyses")

    def __repr__(self) -> str:
        return (
            f"<FireAnalysis id={self.id} user_id={self.user_id} "
            f"score={self.fire_score} age={self.estimated_fire_age}>"
        )
