"""Goals routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.fastapi_app.api.deps import get_current_user, get_session
from app.fastapi_app.schemas.goal import GoalContribute, GoalCreate, GoalRead, GoalUpdate
from app.fastapi_app.services.goal_service import GoalService

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.get("", response_model=list[GoalRead])
def list_goals(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return GoalService(session).list_goals(current_user.id)


@router.post("", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: GoalCreate,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return GoalService(session).create_goal(current_user.id, payload)


@router.put("/{goal_id}", response_model=GoalRead)
def update_goal(
    goal_id: int,
    payload: GoalUpdate,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    goal = GoalService(session).update_goal(current_user.id, goal_id, payload)
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return goal


@router.post("/{goal_id}/contribute", response_model=GoalRead)
def contribute_to_goal(
    goal_id: int,
    payload: GoalContribute,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    goal = GoalService(session).contribute(current_user.id, goal_id, payload)
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    deleted = GoalService(session).delete_goal(current_user.id, goal_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
