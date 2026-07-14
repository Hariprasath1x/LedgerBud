"""Net Worth routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.fastapi_app.api.deps import get_current_user, get_session
from app.fastapi_app.schemas.net_worth import (
    NetWorthItemCreate,
    NetWorthItemRead,
    NetWorthItemUpdate,
    NetWorthSnapshotRead,
    NetWorthSummary,
)
from app.fastapi_app.services.net_worth_service import NetWorthService

router = APIRouter(prefix="/net-worth", tags=["Net Worth"])


@router.get("/summary", response_model=NetWorthSummary)
def get_net_worth_summary(current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    return NetWorthService(session).get_summary(current_user.id)


@router.get("/items", response_model=list[NetWorthItemRead])
def list_net_worth_items(current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    return [NetWorthItemRead.model_validate(item) for item in NetWorthService(session).list_items(current_user.id)]


@router.post("/items", response_model=NetWorthItemRead, status_code=status.HTTP_201_CREATED)
def create_net_worth_item(payload: NetWorthItemCreate, current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    item = NetWorthService(session).create_item(current_user.id, payload)
    return NetWorthItemRead.model_validate(item)


@router.put("/items/{item_id}", response_model=NetWorthItemRead)
def update_net_worth_item(item_id: int, payload: NetWorthItemUpdate, current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    item = NetWorthService(session).update_item(current_user.id, item_id, payload)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return NetWorthItemRead.model_validate(item)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_net_worth_item(item_id: int, current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    deleted = NetWorthService(session).delete_item(current_user.id, item_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")


@router.post("/snapshot", response_model=NetWorthSnapshotRead, status_code=status.HTTP_201_CREATED)
def take_snapshot(current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    snapshot = NetWorthService(session).take_snapshot(current_user.id)
    return NetWorthSnapshotRead.model_validate(snapshot)


@router.get("/history", response_model=list[NetWorthSnapshotRead])
def list_snapshots(current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    return [NetWorthSnapshotRead.model_validate(s) for s in NetWorthService(session).list_snapshots(current_user.id)]
