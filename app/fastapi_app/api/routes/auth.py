"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.fastapi_app.api.deps import get_current_user, get_session
from app.fastapi_app.core.exceptions import AuthenticationError, InactiveUserError, UserAlreadyExistsError
from app.fastapi_app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, TokenResponse, UserRead
from app.fastapi_app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, session: Session = Depends(get_session)) -> AuthResponse:
    service = AuthService(session)
    try:
        user = service.register(payload)
        _, token, expires_in = service.authenticate(LoginRequest(email=payload.email, password=payload.password))
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (AuthenticationError, InactiveUserError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return AuthResponse(
        user=UserRead.model_validate(user),
        token=TokenResponse(access_token=token, expires_in=expires_in),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_session)) -> TokenResponse:
    service = AuthService(session)
    try:
        _, token, expires_in = service.authenticate(payload)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except InactiveUserError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=UserRead)
def me(current_user=Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
