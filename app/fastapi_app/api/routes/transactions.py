"""Transaction CRUD and search routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.fastapi_app.api.deps import get_current_user, get_session
from app.fastapi_app.schemas.transaction import TransactionCreate, TransactionPage, TransactionRead, TransactionUpdate
from app.fastapi_app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=TransactionPage)
def list_transactions(
    wallet_id: int | None = None,
    search: str | None = None,
    category: str | None = None,
    transaction_type: str | None = Query(default=None, alias="type"),
    is_transfer: bool | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    items, total = TransactionService(session).list_transactions(
        current_user.id,
        wallet_id=wallet_id,
        search=search,
        category=category,
        transaction_type=transaction_type,
        is_transfer=is_transfer,
        page=page,
        per_page=per_page,
    )
    return TransactionPage(
        items=[TransactionRead.model_validate(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(payload: TransactionCreate, current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    try:
        transaction = TransactionService(session).create_transaction(current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return TransactionRead.model_validate(transaction)


@router.put("/{transaction_id}", response_model=TransactionRead)
def update_transaction(transaction_id: int, payload: TransactionUpdate, current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    try:
        transaction = TransactionService(session).update_transaction(current_user.id, transaction_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return TransactionRead.model_validate(transaction)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    deleted = TransactionService(session).delete_transaction(current_user.id, transaction_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
