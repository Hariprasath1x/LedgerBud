"""Analytics schemas."""

from pydantic import BaseModel


class TrendPoint(BaseModel):
    month: str
    income: float
    expense: float
    savings: float
    savings_rate: float


class CategoryBreakdown(BaseModel):
    category: str
    amount: float
    count: int
    percentage: float


class MerchantPoint(BaseModel):
    merchant: str
    amount: float
    count: int


class WhatIfRequest(BaseModel):
    category: str | None = None
    reduce_by: float = 0.0
    years: int = 10
    interest_rate: float = 12.0


class WhatIfResponse(BaseModel):
    current_expense: float
    new_expense: float
    current_savings: float
    new_savings: float
    new_savings_rate: float
    yearly_savings: float
    investment_value: float
    reduction: float
    years: int
    interest_rate: float


class AnalyticsSummary(BaseModel):
    trends: list[TrendPoint]
    category_breakdown: list[CategoryBreakdown]
    top_merchants: list[MerchantPoint]
