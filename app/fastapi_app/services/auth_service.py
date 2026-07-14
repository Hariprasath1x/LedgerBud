"""Authentication and identity services."""

from datetime import timedelta

from sqlalchemy.orm import Session

from app.fastapi_app.core.config import settings
from app.fastapi_app.core.exceptions import AuthenticationError, InactiveUserError, UserAlreadyExistsError
from app.fastapi_app.core.security import create_access_token, hash_password, verify_password
from app.fastapi_app.models.user import User
from app.fastapi_app.repositories.user_repository import UserRepository
from app.fastapi_app.schemas.auth import LoginRequest, RegisterRequest
from app.fastapi_app.core.firebase import firebase_sign_in, firebase_sign_up


class AuthService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)

    def register(self, payload: RegisterRequest) -> User:
        existing_user = self.users.get_by_email(payload.email)
        if existing_user:
            raise UserAlreadyExistsError("A user with this email already exists.")

        if settings.use_firebase:
            # Register in Firebase Auth first
            firebase_sign_up(payload.email, payload.password)
            
            # Use a secure random string/dummy for local password hash
            import secrets
            dummy_password = secrets.token_urlsafe(16)
            password_hash = hash_password(dummy_password)
        else:
            password_hash = hash_password(payload.password)

        user = self.users.create(
            full_name=payload.full_name,
            email=payload.email,
            password_hash=password_hash,
        )
        self.session.commit()
        self.session.refresh(user)
        return user

    def authenticate(self, payload: LoginRequest) -> tuple[User, str, int]:
        if settings.use_firebase:
            # Login via Firebase Auth REST API
            fb_res = firebase_sign_in(payload.email, payload.password)
            token = fb_res["idToken"]
            expires_in = int(fb_res.get("expiresIn", settings.access_token_expire_minutes * 60))
            
            user = self.users.get_by_email(payload.email)
            if not user:
                # Auto-provision user record locally if missing
                import secrets
                dummy_password = secrets.token_urlsafe(16)
                password_hash = hash_password(dummy_password)
                full_name = payload.email.split("@")[0]
                user = self.users.create(
                    full_name=full_name,
                    email=payload.email,
                    password_hash=password_hash,
                )
                self.session.commit()
                self.session.refresh(user)
        else:
            user = self.users.get_by_email(payload.email)
            if not user or not verify_password(payload.password, user.password_hash):
                raise AuthenticationError("Invalid email or password.")
            
            expires_in = settings.access_token_expire_minutes * 60
            token = create_access_token(
                subject=str(user.id),
                expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
                extra_claims={"email": user.email, "full_name": user.full_name},
            )

        if not user.is_active:
            raise InactiveUserError("This account is disabled.")

        return user, token, expires_in
