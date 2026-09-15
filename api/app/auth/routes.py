from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.deps import get_auth_service, get_current_user
from app.auth.exceptions import (
    EmailAlreadyRegisteredError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidOrExpiredTokenError,
)
from app.auth.models import User
from app.auth.schemas import ResendVerificationRequest, Token, UserCreate, UserRead
from app.auth.service import AuthService
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate, auth_service: AuthService = Depends(get_auth_service)
) -> User:
    try:
        return await auth_service.register_user(user_in)
    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        ) from None


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    try:
        user = await auth_service.authenticate_user(form_data.username, form_data.password)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        ) from None
    except EmailNotVerifiedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in",
        ) from None

    access_token = create_access_token(subject=user.email)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/verify-email")
async def verify_email_endpoint(
    token: str, auth_service: AuthService = Depends(get_auth_service)
) -> dict[str, str]:
    try:
        await auth_service.verify_email(token)
    except InvalidOrExpiredTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        ) from None
    return {"message": "Email verified successfully"}


@router.post("/resend-verification", status_code=status.HTTP_202_ACCEPTED)
async def resend_verification(
    payload: ResendVerificationRequest, auth_service: AuthService = Depends(get_auth_service)
) -> dict[str, str]:
    await auth_service.resend_verification_email(payload.email)
    return {"message": "If that email is registered and unverified, a new link has been sent"}
