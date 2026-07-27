from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

class BoreholeCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    pixel_x: Decimal

    pixel_y: Decimal

class BoreholeUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    pixel_x: Decimal | None = None

    pixel_y: Decimal | None = None

class BoreholeResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    map_id: int

    name: str

    description: str | None

    pixel_x: Decimal

    pixel_y: Decimal

    longitude: Decimal

    latitude: Decimal
