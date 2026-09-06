"""Реэкспорт моделей, чтобы Alembic видел их все через один импорт."""
from app.models.booking import Booking
from app.models.room import Room
from app.models.user import User

__all__ = ["Booking", "Room", "User"]
