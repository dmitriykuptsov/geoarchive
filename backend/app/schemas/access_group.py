from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class AccessGroupCreateRequest(BaseModel):

    name: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = None


class AccessGroupResponse(BaseModel):

    id: int
    name: str
    description: str | None
    is_active: bool
    created_by: int

    model_config = ConfigDict(
        from_attributes=True,
    )
