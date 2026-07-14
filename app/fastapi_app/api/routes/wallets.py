"""Wallet CRUD routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.fastapi_app.api.deps import get_current_user, get_session
from app.fastapi_app.schemas.wallet import (
    WalletCreate, WalletRead, WalletSummary, WalletUpdate,
    WalletTransferRequest, WalletTransferResponse,
)
from app.fastapi_app.services.wallet_service import WalletService

router = APIRouter(prefix="/wallets", tags=["Wallets"])


@router.get("", response_model=list[WalletRead])
def list_wallets(include_archived: bool = False, current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    return [WalletRead.model_validate(wallet) for wallet in WalletService(session).list_wallets(current_user.id, include_archived)]


@router.get("/summary", response_model=WalletSummary)
def wallet_summary(current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    summary = WalletService(session).wallet_summary(current_user.id)
    return WalletSummary(**summary)


# NOTE: /transfer MUST be declared before /{wallet_id} routes so FastAPI
# does not interpret the literal "transfer" as a wallet_id integer.
@router.post("/transfer", response_model=WalletTransferResponse)
def transfer_funds(payload: WalletTransferRequest, current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    try:
        response = WalletService(session).transfer(
            current_user.id, 
            payload.from_wallet_id, 
            payload.to_wallet_id, 
            payload.amount, 
            payload.notes, 
            payload.transaction_date
        )
        return response
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("", response_model=WalletRead, status_code=status.HTTP_201_CREATED)
def create_wallet(payload: WalletCreate, current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    try:
        wallet = WalletService(session).create_wallet(current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return WalletRead.model_validate(wallet)


@router.put("/{wallet_id}", response_model=WalletRead)
def update_wallet(wallet_id: int, payload: WalletUpdate, current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    try:
        wallet = WalletService(session).update_wallet(current_user.id, wallet_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    return WalletRead.model_validate(wallet)


@router.delete("/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wallet(wallet_id: int, current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    deleted = WalletService(session).delete_wallet(current_user.id, wallet_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")


@router.post("/{wallet_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
def archive_wallet(wallet_id: int, current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    archived = WalletService(session).archive_wallet(current_user.id, wallet_id)
    if not archived:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
