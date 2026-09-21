"""Authentication routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.fastapi_app.api.deps import get_current_user, get_session
from app.fastapi_app.schemas.auth import UserRead

router = APIRouter(prefix="/auth", tags=["Auth"])


from pydantic import BaseModel
from fastapi import HTTPException
from app.fastapi_app.core.firebase import initialize_firebase
from firebase_admin import auth

class NameUpdate(BaseModel):
    full_name: str

@router.get("/me", response_model=UserRead)
def me(current_user=Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)

@router.put("/me/name", response_model=UserRead)
def update_name(payload: NameUpdate, current_user=Depends(get_current_user), session: Session = Depends(get_session)) -> UserRead:
    current_user.full_name = payload.full_name
    session.commit()
    session.refresh(current_user)
    # Attempt to sync with Firebase if initialized
    try:
        initialize_firebase()
        if current_user.firebase_uid:
            auth.update_user(current_user.firebase_uid, display_name=payload.full_name)
    except Exception as e:
        print(f"Warning: Failed to sync name to Firebase: {e}")
    return UserRead.model_validate(current_user)

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    # Delete from Firebase Auth first
    try:
        initialize_firebase()
        if current_user.firebase_uid:
            auth.delete_user(current_user.firebase_uid)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete Firebase identity: {e}")
    
    # Delete from local DB (cascades all data)
    session.delete(current_user)
    session.commit()
