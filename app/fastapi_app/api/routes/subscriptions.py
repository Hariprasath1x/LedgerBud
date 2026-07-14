"""Subscription routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.fastapi_app.api.deps import get_current_user, get_session
from app.fastapi_app.schemas.subscription import SubscriptionCreate, SubscriptionRead, SubscriptionUpdate
from app.fastapi_app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("", response_model=list[SubscriptionRead])
def list_subscriptions(
    confirmed_only: bool = False,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return SubscriptionService(session).list_subscriptions(current_user.id, confirmed_only=confirmed_only)


@router.post("", response_model=SubscriptionRead, status_code=status.HTTP_201_CREATED)
def create_subscription(
    payload: SubscriptionCreate,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return SubscriptionService(session).create_subscription(current_user.id, payload)


@router.put("/{sub_id}", response_model=SubscriptionRead)
def update_subscription(
    sub_id: int,
    payload: SubscriptionUpdate,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    sub = SubscriptionService(session).update_subscription(current_user.id, sub_id, payload)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return sub


@router.post("/{sub_id}/confirm", response_model=SubscriptionRead)
def confirm_subscription(
    sub_id: int,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    sub = SubscriptionService(session).confirm_subscription(current_user.id, sub_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return sub


@router.delete("/{sub_id}", status_code=status.HTTP_204_NO_CONTENT)
def dismiss_subscription(
    sub_id: int,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    dismissed = SubscriptionService(session).dismiss_subscription(current_user.id, sub_id)
    if not dismissed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")


@router.post("/detect", response_model=int)
def detect_and_sync_subscriptions(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Detect new subscriptions from transactions and sync them to database."""
    return SubscriptionService(session).sync_detected(current_user.id)
