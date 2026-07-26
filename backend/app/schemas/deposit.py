from enum import Enum as PyEnum

from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class DepositStatus(str, PyEnum):

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class DepositVisibility(str, PyEnum):

    PRIVATE = "private"
    GROUP = "group"
    PUBLIC = "public"


class DepositCreateRequest(BaseModel):

    name: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    country: str | None = Field(
        default=None,
        max_length=100,
    )

    region: str | None = Field(
        default=None,
        max_length=255,
    )

    status: DepositStatus = (
        DepositStatus.ACTIVE
    )

    visibility: DepositVisibility = (
        DepositVisibility.PRIVATE
    )

    latitude: Decimal | None = Field(
        default=None,
        ge=Decimal("-90"),
        le=Decimal("90"),
    )

    longitude: Decimal | None = Field(
        default=None,
        ge=Decimal("-180"),
        le=Decimal("180"),
    )


class DepositUpdateRequest(BaseModel):

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    country: str | None = Field(
        default=None,
        max_length=100,
    )

    region: str | None = Field(
        default=None,
        max_length=255,
    )

    status: DepositStatus | None = None

    visibility: DepositVisibility | None = None

    latitude: Decimal | None = Field(
        default=None,
        ge=Decimal("-90"),
        le=Decimal("90"),
    )

    longitude: Decimal | None = Field(
        default=None,
        ge=Decimal("-180"),
        le=Decimal("180"),
    )


class DepositResponse(BaseModel):

    id: int
    name: str
    description: str | None
    country: str | None
    region: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    status: DepositStatus
    visibility: DepositVisibility
    created_by: int

    model_config = ConfigDict(
        from_attributes=True,
    )
