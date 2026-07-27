from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.models.enums import MapType


class MapCreate(
    BaseModel,
):

    name: str = Field(
        min_length=1,
        max_length=500,
    )

    description: str | None = None

    map_type: MapType

    coordinate_system: str = Field(
        default="EPSG:4326",
        max_length=50,
    )


class MapUpdate(
    BaseModel,
):

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
    )

    description: str | None = None

    map_type: MapType | None = None

    coordinate_system: str | None = Field(
        default=None,
        max_length=50,
    )


class MapFileResponse(
    BaseModel,
):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    file_type: str

    storage_path: str

    mime_type: str

    file_size: int

    width: int | None

    height: int | None


class MapCalibrationPointCreate(
    BaseModel,
):

    pixel_x: Decimal

    pixel_y: Decimal

    longitude: Decimal = Field(
        ge=Decimal("-180"),
        le=Decimal("180"),
    )

    latitude: Decimal = Field(
        ge=Decimal("-90"),
        le=Decimal("90"),
    )


class MapCalibrationPointUpdate(
    BaseModel,
):
    pixel_x: Decimal | None = None

    pixel_y: Decimal | None = None

    longitude: Decimal | None = Field(
        default=None,
        ge=Decimal("-180"),
        le=Decimal("180"),
    )

    latitude: Decimal | None = Field(
        default=None,
        ge=Decimal("-90"),
        le=Decimal("90"),
    )


class MapCalibrationPointResponse(
    BaseModel,
):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    map_id: int

    pixel_x: Decimal

    pixel_y: Decimal

    longitude: Decimal

    latitude: Decimal


class MapResponse(
    BaseModel,
):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    deposit_id: int

    name: str

    description: str | None

    map_type: MapType

    coordinate_system: str

    created_by: int


class MapUpdate(
    BaseModel,
):

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
    )

    description: str | None = None

    map_type: MapType | None = None

    coordinate_system: str | None = Field(
        default=None,
        max_length=50,
    )

class CalibrationErrorResponse(
    BaseModel,
):
    rmse_meters: float
    max_error_meters: float

class AffineTransformationResponse(BaseModel):
    longitude_coefficients: tuple[
        float,
        float,
        float,
    ]

    latitude_coefficients: tuple[
        float,
        float,
        float,
    ]

    error: CalibrationErrorResponse

