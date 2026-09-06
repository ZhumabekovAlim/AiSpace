"""Регистрация, вход, профиль, привязка Telegram."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserProfile, UserUpdate
from app.services import link_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _profile(user: User) -> UserProfile:
    data = UserProfile.model_validate(user)
    data.telegram_linked = user.telegram_id is not None
    return data


@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> UserProfile:
    exists = await db.scalar(select(User).where(User.email == payload.email))
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует",
        )
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        phone=payload.phone,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email или телефоном уже существует",
        ) from exc
    await db.refresh(user)
    return _profile(user)


@router.post("/login", response_model=Token)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    # OAuth2PasswordRequestForm использует поле "username" — сюда кладём email.
    user = await db.scalar(select(User).where(User.email == form.username))
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )
    return Token(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserProfile)
async def me(current_user: User = Depends(get_current_user)) -> UserProfile:
    return _profile(current_user)


@router.patch("/me", response_model=UserProfile)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(current_user, field, value)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Такой телефон уже привязан к другому аккаунту",
        ) from exc
    await db.refresh(current_user)
    return _profile(current_user)


@router.post("/me/telegram-code", response_model=dict)
async def telegram_link_code(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Генерирует одноразовый код для привязки Telegram (отправить боту /link <код>)."""
    code = await link_service.generate_link_code(db, current_user)
    return {"code": code}
