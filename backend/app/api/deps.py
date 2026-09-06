"""Общие зависимости FastAPI: текущий пользователь и проверка роли."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole

# tokenUrl — путь логина, нужен для кнопки Authorize в Swagger UI.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

_credentials_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Не удалось подтвердить учётные данные",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = decode_access_token(token)
    if user_id is None:
        raise _credentials_error

    user = await db.get(User, int(user_id))
    if user is None or not user.is_active:
        raise _credentials_error
    return user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Пропускает только администратора (управление комнатами, отмена чужих броней)."""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора",
        )
    return current_user
