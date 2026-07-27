from pydantic import BaseModel


class GroupMemberCreateRequest(BaseModel):
    user_id: int
