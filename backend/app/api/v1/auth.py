from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db_session
from ...core.jwt import create_access_token
from ...core.security import hash_password, verify_password
from ...models.user import User
from ...schemas.auth import (
    ForgotPasswordLogin,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from ..dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    data: UserCreate,
    session: AsyncSession = Depends(get_db_session),
) -> User:
    stmt = select(User).where(User.email == data.email)
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    user = User(
        email=data.email,
        name=data.name,
        hashed_password=hash_password(data.password),
        birth_date=data.birth_date,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/forgot-password", response_model=TokenResponse)
async def forgot_password_login(
    data: ForgotPasswordLogin,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    stmt = select(User).where(User.email == data.email)
    user = (await session.execute(stmt)).scalar_one_or_none()
    if not user or user.birth_date is None or user.birth_date != data.birth_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification failed: Email or Birth Date does not match our records",
        )

    if data.new_password:
        user.hashed_password = hash_password(data.new_password)
        await session.commit()
        await session.refresh(user)

    token = create_access_token(user_id=user.id, email=user.email)
    return TokenResponse(access_token=token, user_name=user.name)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    stmt = select(User).where(User.email == data.email)
    user = (await session.execute(stmt)).scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user_id=user.id, email=user.email)
    return TokenResponse(access_token=token, user_name=user.name)


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)) -> User:
    return user
