"""Subscription schemas."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class SubscriptionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    merchant_name: str | None = Field(default=None, max_length=200)
    amount: float = Field(gt=0)
    frequency: str = Field(default="monthly", pattern="^(daily|weekly|monthly|quarterly|yearly)$")
    category: str | None = Field(default=None, max_length=100)
    last_detected: date | None = None
    next_expected: date | None = None
    detection_confidence: float | None = Field(default=None, ge=0, le=1)


class SubscriptionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    amount: float | None = Field(default=None, gt=0)
    frequency: str | None = Field(default=None, pattern="^(daily|weekly|monthly|quarterly|yearly)$")
    category: str | None = Field(default=None, max_length=100)
    is_confirmed: bool | None = None
    is_active: bool | None = None


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    merchant_name: str | None
    amount: float
    frequency: str
    category: str | None
    last_detected: date | None
    next_expected: date | None
    is_confirmed: bool
    is_active: bool
    detection_confidence: float | None
    yearly_cost: float
    created_at: datetime
