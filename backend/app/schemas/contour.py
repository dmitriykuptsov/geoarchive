from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

class ContourPointCreate(BaseModel):
    pixel_x: Decimal
    pixel_y: Decimal

class ContourPointResponse(BaseModel):
    pixel_x: Decimal
    pixel_y: Decimal
    longitude: Decimal
    latitude: Decimal

class ContourCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    points: list[ContourPointCreate] = Field(
        min_length=2,
    )

class ContourUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    points: list[ContourPointCreate] | None = Field(
        default=None,
        min_length=2,
    )

class ContourResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    map_id: int
    name: str
    description: str | None
    points: list[ContourPointResponse]