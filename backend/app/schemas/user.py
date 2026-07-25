from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=100,
    )

    email: EmailStr | None = None

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    role_ids: list[int] = Field(
        min_length=1,
    )


class UserResponse(BaseModel):

    id: int
    username: str
    email: str | None
    is_active: bool
    must_change_password: bool

    model_config = {
        "from_attributes": True,
    }


class UserListResponse(BaseModel):

    items: list[UserResponse]
    total: int


class UserUpdateRequest(BaseModel):

    email: EmailStr | None = None

    is_active: bool | None = None

    role_ids: list[int] | None = None