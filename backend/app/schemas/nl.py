from datetime import datetime

from pydantic import BaseModel, Field


class NLParseRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class NLBookingDraft(BaseModel):
    """Черновик брони, распознанный из фразы. В БД НЕ пишется —
    возвращается на подтверждение пользователю (предзаполненная форма).
    """

    room_id: int | None = None
    room_name: str | None = None  # что распознала модель, для подсказки в UI
    title: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None

    # Чего не хватило для однозначной брони (например ["room", "start_time"]).
    missing: list[str] = Field(default_factory=list)
    # Человеческая подсказка/уточняющий вопрос от модели.
    clarification: str | None = None
