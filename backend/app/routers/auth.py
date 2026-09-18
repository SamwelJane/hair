from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.rate_limit import get_client_ip, rate_limit
from app.db.session import get_db
from app.models.identity import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenPair,
    UserOut,
)
from app.services import auth as auth_service
from app.services.notifications.email import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)) -> TokenPair:
    ip = get_client_ip(dict(request.headers), request.client.host if request.client else None)
    if not await rate_limit(f"register:{ip}", limit=5, window_seconds=3600):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many attempts")

    try:
        user = await auth_service.register_user(
            db, name=payload.name, email=payload.email, password=payload.password, phone=payload.phone
        )
    except auth_service.EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered") from exc

    access_token, refresh_token = await auth_service.issue_token_pair(db, user)
    return TokenPair(access_token=access_token, refresh_token=refresh_token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)) -> TokenPair:
    ip = get_client_ip(dict(request.headers), request.client.host if request.client else None)
    rate_key = f"login:{payload.email.lower()}:{ip}"
    if not await rate_limit(rate_key, limit=5, window_seconds=900):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many attempts")

    try:
        user = await auth_service.authenticate_user(db, email=payload.email, password=payload.password)
    except auth_service.InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password") from exc

    access_token, refresh_token = await auth_service.issue_token_pair(db, user)
    return TokenPair(access_token=access_token, refresh_token=refresh_token, user=UserOut.model_validate(user))


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    try:
        access_token, refresh_token, user = await auth_service.rotate_refresh_token(db, payload.refresh_token)
    except auth_service.InvalidRefreshTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    return TokenPair(access_token=access_token, refresh_token=refresh_token, user=UserOut.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> None:
    await auth_service.revoke_refresh_token(db, payload.refresh_token)


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)) -> dict[str, bool]:
    result = await auth_service.request_password_reset(db, payload.email)
    if result is not None:
        user, raw_token = result
        await send_password_reset_email(user.email, raw_token)
    # Always the same response, whether or not the email exists - avoids
    # account enumeration, matching the old app's forgot-password behavior.
    return {"ok": True}


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)) -> None:
    try:
        await auth_service.reset_password(db, token=payload.token, new_password=payload.password)
    except auth_service.InvalidResetTokenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token") from exc


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)
