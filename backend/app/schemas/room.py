from pydantic import BaseModel, ConfigDict, Field


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    capacity: int = Field(default=0, ge=0)
    description: str | None = None


class RoomUpdate(BaseModel):
    """Частичное обновление: все поля опциональны (PATCH-семантика)."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    capacity: int | None = Field(default=None, ge=0)
    description: str | None = None
    is_active: bool | None = None


class RoomRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    capacity: int
    description: str | None
    is_active: bool
