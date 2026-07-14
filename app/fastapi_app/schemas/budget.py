"""Budget schemas."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class BudgetCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    category: str = Field(min_length=2, max_length=100)
    amount: float = Field(gt=0)
    period: str = Field(default="monthly", pattern="^(daily|weekly|monthly|quarterly|yearly)$")
    start_date: date | None = None


class BudgetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    category: str | None = Field(default=None, min_length=2, max_length=100)
    amount: float | None = Field(default=None, gt=0)
    period: str | None = Field(default=None, pattern="^(daily|weekly|monthly|quarterly|yearly)$")
    is_active: bool | None = None


class BudgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    category: str
    amount: float
    period: str
    start_date: date | None
    is_active: bool
    created_at: datetime


class BudgetWithUsage(BudgetRead):
    spent: float = 0.0
    remaining: float = 0.0
    utilization_pct: float = 0.0
    is_exceeded: bool = False
    status: str = "healthy"  # healthy, warning, exceeded
