from enum import Enum as PyEnum

from pydantic import BaseModel, ConfigDict


class DepositAccessLevel(str, PyEnum):

    VIEW = "view"
    EDIT = "edit"
    ADMIN = "admin"


class DepositAccessCreateRequest(BaseModel):

    access_level: DepositAccessLevel = DepositAccessLevel.VIEW


class DepositAccessResponse(BaseModel):

    id: int
    deposit_id: int
    group_id: int
    access_level: DepositAccessLevel

    model_config = ConfigDict(
        from_attributes=True,
    )


class DepositAccessLevel(str, PyEnum):

    VIEW = "view"
    EDIT = "edit"
    ADMIN = "admin"


class DepositAccessCreateRequest(BaseModel):

    group_id: int
    access_level: DepositAccessLevel = DepositAccessLevel.VIEW
