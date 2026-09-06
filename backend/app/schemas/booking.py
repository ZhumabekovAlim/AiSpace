from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.amenities import AMENITY_IDS


class BookingCreate(BaseModel):
    room_id: int
    title: str = Field(min_length=1, max_length=255)
    comment: str | None = Field(default=None, max_length=2000)
    amenities: list[str] = Field(default_factory=list)
    # Ожидаем datetime с таймзоной (ISO 8601, напр. 2026-09-07T14:00:00+05:00).
    start_time: datetime
    end_time: datetime

    @field_validator("amenities")
    @classmethod
    def _known_amenities(cls, value: list[str]) -> list[str]:
        unknown = set(value) - AMENITY_IDS
        if unknown:
            raise ValueError(f"Неизвестные допы: {', '.join(sorted(unknown))}")
        return sorted(set(value))  # убираем дубли, стабильный порядок

    @model_validator(mode="after")
    def _check_interval(self) -> "BookingCreate":
        if self.start_time.tzinfo is None or self.end_time.tzinfo is None:
            raise ValueError("start_time и end_time должны быть с таймзоной")
        if self.end_time <= self.start_time:
            raise ValueError("end_time должен быть позже start_time")
        return self


class BookingUserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    user_id: int
    title: str
    comment: str | None
    amenities: list[str]
    start_time: datetime
    end_time: datetime
    created_at: datetime


class AmenityRead(BaseModel):
    id: str
    label: str
    icon: str
