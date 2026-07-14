"""Budget routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.fastapi_app.api.deps import get_current_user, get_session
from app.fastapi_app.schemas.budget import BudgetCreate, BudgetRead, BudgetUpdate, BudgetWithUsage
from app.fastapi_app.services.budget_service import BudgetService

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get("", response_model=list[BudgetWithUsage])
def list_budgets(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return BudgetService(session).list_budgets(current_user.id)


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(
    payload: BudgetCreate,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return BudgetService(session).create_budget(current_user.id, payload)


@router.put("/{budget_id}", response_model=BudgetRead)
def update_budget(
    budget_id: int,
    payload: BudgetUpdate,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    budget = BudgetService(session).update_budget(current_user.id, budget_id, payload)
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    deleted = BudgetService(session).delete_budget(current_user.id, budget_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
