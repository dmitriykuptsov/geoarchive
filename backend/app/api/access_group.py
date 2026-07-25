from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_db,
    require_password_changed,
    require_global_admin
)

from app.models.group_member import GroupMember
from app.models.access_group import AccessGroup
from app.models.user import User
from app.models.deposit import Deposit
from app.models.deposit_access import DepositAccess

from app.schemas.access_group import (
    AccessGroupCreateRequest,
    AccessGroupResponse,
)

from app.schemas.group_member import (
    GroupMemberCreateRequest
)

from app.schemas.deposit_access import (
    DepositAccessCreateRequest,
    DepositAccessResponse,
)

router = APIRouter()


@router.post(
    "",
    response_model=AccessGroupResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_access_group(
    request: AccessGroupCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_global_admin,
    ),
) -> AccessGroup:

    existing_group = db.scalar(
        select(AccessGroup).where(
            AccessGroup.name == request.name,
        )
    )

    if existing_group is not None:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "An access group with this name "
                "already exists"
            ),
        )

    access_group = AccessGroup(
        name=request.name,
        description=request.description,
        created_by=current_user.id,
    )

    db.add(access_group)
    db.commit()
    db.refresh(access_group)

    return access_group


@router.post(
    "/{group_id}/members",
    status_code=status.HTTP_201_CREATED,
)
def add_group_member(
    group_id: int,
    request: GroupMemberCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_global_admin,
    ),
):
    group = db.scalar(
        select(AccessGroup).where(
            AccessGroup.id == group_id,
            AccessGroup.is_active.is_(True),
        )
    )

    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access group not found",
        )

    user = db.scalar(
        select(User).where(
            User.id == request.user_id,
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    existing_member = db.scalar(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == request.user_id,
        )
    )

    if existing_member is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this group",
        )

    member = GroupMember(
        group_id=group_id,
        user_id=request.user_id,
    )

    db.add(member)
    db.commit()
    db.refresh(member)

    return member


@router.get(
    "/{group_id}/members",
)
def list_group_members(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_global_admin,
    ),
):
    group = db.scalar(
        select(AccessGroup).where(
            AccessGroup.id == group_id,
        )
    )

    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access group not found",
        )

    members = db.scalars(
        select(GroupMember)
        .where(
            GroupMember.group_id == group_id,
        )
        .order_by(
            GroupMember.created_at,
        )
    ).all()

    return members

@router.delete(
    "/{group_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_group_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_global_admin,
    ),
):
    member = db.scalar(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
    )

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group membership not found",
        )

    db.delete(member)
    db.commit()


@router.post(
    "/{group_id}/deposits/{deposit_id}",
    response_model=DepositAccessResponse,
    status_code=status.HTTP_201_CREATED,
)
def grant_deposit_access(
    group_id: int,
    deposit_id: int,
    request: DepositAccessCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_global_admin,
    ),
) -> DepositAccess:

    group = db.scalar(
        select(AccessGroup).where(
            AccessGroup.id == group_id,
            AccessGroup.is_active.is_(True),
        )
    )

    if group is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access group not found",
        )

    deposit = db.scalar(
        select(Deposit).where(
            Deposit.id == deposit_id,
        )
    )

    if deposit is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deposit not found",
        )

    existing_access = db.scalar(
        select(DepositAccess).where(
            DepositAccess.group_id == group_id,
            DepositAccess.deposit_id == deposit_id,
        )
    )

    if existing_access is not None:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This group already has access "
                "to this deposit"
            ),
        )

    access = DepositAccess(
        group_id=group_id,
        deposit_id=deposit_id,
        access_level=request.access_level.value,
    )

    db.add(access)

    db.commit()

    db.refresh(access)

    return access


@router.get(
    "/{group_id}/deposits",
    response_model=list[DepositAccessResponse],
)
def list_group_deposit_access(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_global_admin,
    ),
) -> list[DepositAccess]:

    group = db.scalar(
        select(AccessGroup).where(
            AccessGroup.id == group_id,
        )
    )

    if group is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access group not found",
        )

    access_rules = db.scalars(
        select(DepositAccess)
        .where(
            DepositAccess.group_id == group_id,
        )
        .order_by(
            DepositAccess.created_at,
        )
    ).all()

    return access_rules


@router.delete(
    "/{group_id}/deposits/{deposit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def revoke_deposit_access(
    group_id: int,
    deposit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_global_admin,
    ),
) -> None:

    access = db.scalar(
        select(DepositAccess).where(
            DepositAccess.group_id == group_id,
            DepositAccess.deposit_id == deposit_id,
        )
    )

    if access is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Deposit access rule not found"
            ),
        )

    db.delete(access)

    db.commit()