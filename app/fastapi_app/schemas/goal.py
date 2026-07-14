"""Goal schemas."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class GoalCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    target_amount: float = Field(gt=0)
    current_amount: float = Field(default=0.0, ge=0)
    target_date: date | None = None


class GoalUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    target_amount: float | None = Field(default=None, gt=0)
    target_date: date | None = None
    status: str | None = Field(default=None, pattern="^(active|completed|paused)$")


class GoalContribute(BaseModel):
    amount: float = Field(gt=0)


class GoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    description: str | None
    target_amount: float
    current_amount: float
    target_date: date | None
    status: str
    created_at: datetime
    updated_at: datetime
    progress_percentage: float
    remaining_amount: float
