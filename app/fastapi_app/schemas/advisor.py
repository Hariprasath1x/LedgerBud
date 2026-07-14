"""AI Advisor schemas."""

from pydantic import BaseModel, Field


class AdvisorRequest(BaseModel):
    question: str = Field(..., max_length=500)
    history: list[dict] | None = None


class AdvisorResponse(BaseModel):
    answer: str
    context_summary: dict
    provider: str
