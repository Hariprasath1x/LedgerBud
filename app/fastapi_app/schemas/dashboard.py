"""Dashboard and intelligence schemas."""

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_income: float
    total_expense: float
    savings: float
    wallet_balance: float


class MonthlySeriesPoint(BaseModel):
    month: str
    income: float
    expense: float
    savings: float
    savings_rate: float


class CategoryPoint(BaseModel):
    category: str
    amount: float
    count: int
    percentage: float


class HealthScoreBreakdown(BaseModel):
    savings_ratio: int
    budget_discipline: int
    spending_behavior: int


class HealthScoreResponse(BaseModel):
    score: int
    grade: str
    label: str
    breakdown: HealthScoreBreakdown
    suggestions: list[str]


class InsightItem(BaseModel):
    type: str          # Old style or new severity: "spike"|"mom_change"|"budget_risk"|"savings_decline"|...
    severity: str = "info"  # "high"|"medium"|"low"|"info"
    title: str
    message: str | None = None  # Backward compat alias for explanation
    explanation: str | None = None
    metric: str | None = None
    value: float | None = None
    recommended_action: str | None = None


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    monthly_trends: list[MonthlySeriesPoint]
    category_breakdown: list[CategoryPoint]
    top_merchants: list[dict[str, float | int | str]]
    health_score: HealthScoreResponse
    insights: list[InsightItem]
