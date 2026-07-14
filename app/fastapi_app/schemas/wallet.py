"""Wallet schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WalletCreate(BaseModel):
    wallet_name: str = Field(min_length=2, max_length=120)
    wallet_type: str = Field(min_length=2, max_length=30)
    balance: float = Field(default=0, ge=0)


class WalletUpdate(BaseModel):
    wallet_name: str | None = Field(default=None, min_length=2, max_length=120)
    wallet_type: str | None = Field(default=None, min_length=2, max_length=30)
    balance: float | None = Field(default=None, ge=0)


class WalletRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    wallet_name: str
    wallet_type: str
    balance: float
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class WalletSummary(BaseModel):
    total_wallets: int
    total_balance: float
    by_type: dict[str, float]


class WalletTransferRequest(BaseModel):
    from_wallet_id: int
    to_wallet_id: int
    amount: float = Field(gt=0)
    notes: str | None = None
    transaction_date: str | None = None


class WalletTransferResponse(BaseModel):
    debit_transaction_id: int
    credit_transaction_id: int
    amount: float
    from_wallet_balance: float
    to_wallet_balance: float
