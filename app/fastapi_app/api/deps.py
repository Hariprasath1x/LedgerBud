"""FastAPI dependencies."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.fastapi_app.db.session import get_db
from app.fastapi_app.repositories.user_repository import UserRepository
from app.fastapi_app.core.firebase import verify_firebase_token
from app.fastapi_app.core.exceptions import AuthenticationError


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_session(db: Session = Depends(get_db)) -> Session:
    return db


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_db),
):
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_repo = UserRepository(session)

    try:
        payload = verify_firebase_token(token)
        firebase_uid = payload.get("uid")
        email = payload.get("email")
        if not firebase_uid or not email:
            raise credentials_error
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Firebase authentication failed: {str(exc)}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except Exception:
        raise credentials_error from None

    # First attempt to find user by firebase_uid (the stable identifier)
    user = user_repo.get_by_firebase_uid(firebase_uid)
    
    if not user:
        # Fallback: look up by email to link legacy accounts
        user = user_repo.get_by_email(email)
        if user:
            # Update legacy account with firebase_uid
            user.firebase_uid = firebase_uid
            session.commit()
            session.refresh(user)
        else:
            # Provision a new user record
            full_name = payload.get("name") or email.split("@")[0]
            try:
                user = user_repo.create(
                    full_name=full_name,
                    email=email,
                    firebase_uid=firebase_uid,
                )
                session.commit()
                session.refresh(user)
            except Exception as e:
                session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Could not provision local user: {str(e)}"
                ) from e

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    return user
