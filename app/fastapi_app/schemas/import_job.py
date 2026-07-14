"""ImportJob schemas."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ImportJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    wallet_id: int | None
    original_filename: str
    file_type: str
    status: str
    institution_detected: str | None
    account_number_detected: str | None
    statement_period_start: date | None
    statement_period_end: date | None
    total_records: int
    imported_count: int
    duplicate_count: int
    failed_count: int
    error_message: str | None
    preview_data: dict | None
    created_at: datetime
    completed_at: datetime | None


class ImportPreviewTransaction(BaseModel):
    date: str
    description: str
    amount: float
    transaction_type: str
    merchant_name: str | None = None
    category: str | None = None
    is_duplicate: bool = False


class ImportPreviewResponse(BaseModel):
    job_id: int
    status: str
    institution: str | None
    period_start: str | None
    period_end: str | None
    total_records: int
    unique_count: int
    duplicate_count: int
    failed_count: int
    transactions: list[ImportPreviewTransaction]


class ImportCommitResponse(BaseModel):
    job_id: int
    imported_count: int
    duplicate_count: int
    total_records: int
    status: str
