from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.exceptions import (
    EmailAlreadyRegisteredError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidOrExpiredTokenError,
)
from app.auth.models import EmailVerificationToken, User
from app.auth.schemas import UserCreate
from app.core.config import get_settings
from app.core.email import send_email
from app.core.security import generate_token, hash_password, hash_token, verify_password


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def register_user(self, user_in: UserCreate) -> User:
        existing = await self.get_user_by_email(user_in.email)
        if existing is not None:
            raise EmailAlreadyRegisteredError

        user = User(email=user_in.email, hashed_password=hash_password(user_in.password))
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        await self.send_verification_email(user)
        return user

    async def authenticate_user(self, email: str, password: str) -> User:
        user = await self.get_user_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError
        if not user.is_verified:
            raise EmailNotVerifiedError
        return user

    async def send_verification_email(self, user: User) -> None:
        settings = get_settings()
        raw_token, hashed = generate_token()

        token = EmailVerificationToken(
            user_id=user.id,
            token_hash=hashed,
            expires_at=datetime.now(UTC)
            + timedelta(hours=settings.email_verification_token_expire_hours),
        )
        self.db.add(token)
        await self.db.commit()

        verify_url = f"{settings.frontend_url}/verify-email?token={raw_token}"
        await send_email(
            to=user.email,
            subject="Verify your PulseWatch email",
            html_body=f"<p>Click to verify: <a href='{verify_url}'>{verify_url}</a></p>",
        )

    async def verify_email(self, raw_token: str) -> User:
        hashed = hash_token(raw_token)
        result = await self.db.execute(
            select(EmailVerificationToken).where(EmailVerificationToken.token_hash == hashed)
        )
        token = result.scalar_one_or_none()

        if token is None or token.used_at is not None or token.expires_at < datetime.now(UTC):
            raise InvalidOrExpiredTokenError

        token.used_at = datetime.now(UTC)
        user = await self.db.get(User, token.user_id)
        user.is_verified = True
        await self.db.commit()
        return user

    async def resend_verification_email(self, email: str) -> None:
        user = await self.get_user_by_email(email)

        # Don't reveal whether the email exists — same response either way
        if user is None or user.is_verified:
            return

        # Invalidate any previously issued, unused tokens for this user
        await self.db.execute(
            delete(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user.id,
                EmailVerificationToken.used_at.is_(None),
            )
        )

        await self.send_verification_email(user)
