"""FastAPI dependencies."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.fastapi_app.core.config import settings
from app.fastapi_app.core.security import decode_access_token
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

    if settings.use_firebase:
        try:
            payload = verify_firebase_token(token)
            email = payload.get("email")
            if not email:
                raise credentials_error
        except AuthenticationError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Firebase authentication failed: {str(exc)}",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        except Exception:
            raise credentials_error from None

        user = user_repo.get_by_email(email)
        if not user:
            # Auto-provision user record locally if it doesn't exist yet
            import secrets
            from app.fastapi_app.core.security import hash_password
            dummy_password = secrets.token_urlsafe(16)
            password_hash = hash_password(dummy_password)
            full_name = payload.get("name") or email.split("@")[0]
            try:
                user = user_repo.create(
                    full_name=full_name,
                    email=email,
                    password_hash=password_hash,
                )
                session.commit()
                session.refresh(user)
            except Exception as e:
                session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Could not provision local user: {str(e)}"
                ) from e
    else:
        try:
            payload = decode_access_token(token)
            subject = payload.get("sub")
            user_id = int(subject)
        except (InvalidTokenError, TypeError, ValueError):
            raise credentials_error from None

        user = user_repo.get_by_id(user_id)

    if not user:
        raise credentials_error
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    return user
