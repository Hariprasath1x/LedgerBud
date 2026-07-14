"""Net worth schemas."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class NetWorthItemCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    item_type: str = Field(pattern="^(asset|liability)$")
    category: str = Field(max_length=100)
    amount: float = Field(ge=0)
    notes: str | None = None


class NetWorthItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    item_type: str | None = Field(default=None, pattern="^(asset|liability)$")
    category: str | None = Field(default=None, max_length=100)
    amount: float | None = Field(default=None, ge=0)
    notes: str | None = None


class NetWorthItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    item_type: str
    category: str
    amount: float
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class NetWorthSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    snapshot_date: date
    total_assets: float
    total_liabilities: float
    net_worth: float
    created_at: datetime


class CategoryTotal(BaseModel):
    category: str
    amount: float


class NetWorthSummary(BaseModel):
    total_assets: float
    total_liabilities: float
    net_worth: float
    asset_categories: list[CategoryTotal]
    liability_categories: list[CategoryTotal]
    items: list[NetWorthItemRead]
