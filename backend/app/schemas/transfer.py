from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.amenities import AMENITY_IDS
from app.models.transfer import TransferStatus
from app.schemas.booking import UserBrief


class TransferRequestCreate(BaseModel):
    booking_id: int
    # Желаемые изменения получателя (все опциональны).
    new_title: str | None = Field(default=None, max_length=255)
    new_comment: str | None = Field(default=None, max_length=2000)
    new_amenities: list[str] | None = None
    new_start_time: datetime | None = None
    new_end_time: datetime | None = None

    @field_validator("new_amenities")
    @classmethod
    def _known(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        unknown = set(value) - AMENITY_IDS
        if unknown:
            raise ValueError(f"Неизвестные допы: {', '.join(sorted(unknown))}")
        return sorted(set(value))

    @model_validator(mode="after")
    def _check_times(self) -> "TransferRequestCreate":
        s, e = self.new_start_time, self.new_end_time
        if (s is None) != (e is None):
            raise ValueError("Укажите и начало, и конец нового времени вместе")
        if s is not None and e is not None:
            if s.tzinfo is None or e.tzinfo is None:
                raise ValueError("Время должно быть с таймзоной")
            if e <= s:
                raise ValueError("Конец должен быть позже начала")
        return self


class TransferBookingBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    room_id: int
    start_time: datetime
    end_time: datetime


class TransferRead(BaseModel):
    id: int
    status: TransferStatus
    created_at: datetime
    resolved_at: datetime | None
    room_name: str
    booking: TransferBookingBrief
    from_user: UserBrief
    to_user: UserBrief
    new_title: str | None
    new_comment: str | None
    new_amenities: list[str] | None
    new_start_time: datetime | None
    new_end_time: datetime | None

    @classmethod
    def from_orm_transfer(cls, t) -> "TransferRead":
        """Собирает DTO из ORM-объекта с подгруженными связями."""
        return cls(
            id=t.id,
            status=t.status,
            created_at=t.created_at,
            resolved_at=t.resolved_at,
            room_name=t.booking.room.name,
            booking=TransferBookingBrief.model_validate(t.booking),
            from_user=UserBrief.model_validate(t.from_user),
            to_user=UserBrief.model_validate(t.to_user),
            new_title=t.new_title,
            new_comment=t.new_comment,
            new_amenities=t.new_amenities,
            new_start_time=t.new_start_time,
            new_end_time=t.new_end_time,
        )
