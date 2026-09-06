from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BookingCreate(BaseModel):
    room_id: int
    title: str = Field(min_length=1, max_length=255)
    # Ожидаем datetime с таймзоной (ISO 8601, напр. 2026-09-07T14:00:00+05:00).
    start_time: datetime
    end_time: datetime

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
    start_time: datetime
    end_time: datetime
    created_at: datetime
