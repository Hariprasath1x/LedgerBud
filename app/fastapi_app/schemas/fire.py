"""Pydantic schemas for the FIRE Intelligence Engine."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ── User-configurable settings ─────────────────────────────────────────────


class FireSettings(BaseModel):
    current_age: int = Field(default=25, ge=18, le=80, description="User's current age")
    retirement_target_age: int = Field(default=45, ge=25, le=90, description="Target retirement age")
    investment_return: float = Field(default=12.0, ge=1.0, le=30.0, description="Expected annual investment return %")
    inflation_rate: float = Field(default=6.0, ge=0.0, le=20.0, description="Expected annual inflation rate %")
    lifestyle: Literal["Lean", "Moderate", "Comfortable", "Luxury"] = Field(
        default="Moderate", description="Desired retirement lifestyle"
    )


# ── Wealth projection ──────────────────────────────────────────────────────


class WealthProjectionPoint(BaseModel):
    year: int
    age: int
    nominal_wealth: float
    real_wealth: float          # inflation-adjusted
    target_corpus: float


# ── Scenario analysis ─────────────────────────────────────────────────────


class FireScenario(BaseModel):
    name: str                           # Conservative / Moderate / Aggressive
    expected_return: float
    inflation_rate: float
    fire_target_corpus: float
    estimated_fire_age: float
    years_remaining: float
    monthly_investment_required: float


# ── Score breakdown ───────────────────────────────────────────────────────


class FireScoreBreakdown(BaseModel):
    savings_rate_score: float           # max 30
    health_score_contribution: float    # max 25
    debt_ratio_score: float             # max 15
    net_worth_growth_score: float       # max 15
    investment_discipline_score: float  # max 10
    budget_discipline_score: float      # max 5


# ── Full FIRE calculation result ──────────────────────────────────────────


class FireCalculationResult(BaseModel):
    # Inputs
    settings: FireSettings

    # Auto-fetched financials
    current_net_worth: float
    total_assets: float
    total_liabilities: float
    annual_income: float
    annual_expenses: float
    annual_savings: float
    monthly_income: float
    monthly_expenses: float
    monthly_savings: float
    savings_rate: float                 # %
    debt_ratio: float                   # %
    financial_health_score: float

    # FIRE outputs
    fire_target_corpus: float
    fire_progress: float                # %
    fire_score: float                   # 0–100
    score_breakdown: FireScoreBreakdown
    estimated_fire_age: float
    years_remaining: float
    required_monthly_investment: float

    # Detailed
    wealth_projection: list[WealthProjectionPoint]
    scenarios: list[FireScenario]
    strengths: list[str]
    weaknesses: list[str]

    # Context extras
    subscription_monthly_total: float
    goal_progress_avg: float            # % average across active goals
    top_expense_category: str
    status_label: str                   # On Track / Behind / Critical / Achieved


# ── Dashboard response (from GET /fire) ───────────────────────────────────


class FireDashboardResponse(BaseModel):
    has_data: bool
    result: FireCalculationResult | None = None
    last_calculated: datetime | None = None


# ── History item ──────────────────────────────────────────────────────────


class FireHistoryItem(BaseModel):
    id: int
    current_age: int
    retirement_target_age: int
    fire_score: float
    fire_progress: float
    estimated_fire_age: float
    required_monthly_investment: float
    annual_income: float
    annual_expenses: float
    savings_rate: float
    created_at: datetime

    model_config = {"from_attributes": True}


# ── AI FIRE Coach ─────────────────────────────────────────────────────────


class FireAIRequest(BaseModel):
    question: str = Field(..., max_length=500)
    history: list[dict] | None = None
    fire_context: dict | None = None    # pass pre-built context to avoid double-fetching


class FireAIResponse(BaseModel):
    answer: str
    context_summary: dict
    provider: str
