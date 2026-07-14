"""Transaction schemas."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreate(BaseModel):
    wallet_id: int
    merchant_name: str = Field(min_length=2, max_length=200)
    category: str | None = Field(default=None, max_length=100)
    amount: float
    transaction_type: str = Field(min_length=3, max_length=20)
    notes: str | None = None
    transaction_date: date


class TransactionUpdate(BaseModel):
    wallet_id: int | None = None
    merchant_name: str | None = Field(default=None, min_length=2, max_length=200)
    category: str | None = Field(default=None, max_length=100)
    amount: float | None = None
    transaction_type: str | None = Field(default=None, min_length=3, max_length=20)
    notes: str | None = None
    transaction_date: date | None = None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    wallet_id: int
    merchant_name: str
    category: str | None
    amount: float
    transaction_type: str
    notes: str | None
    transaction_date: date
    is_transfer: bool = False
    created_at: datetime


class TransactionPage(BaseModel):
    items: list[TransactionRead]
    total: int
    page: int
    per_page: int
