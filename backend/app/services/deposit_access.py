from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.access_group import AccessGroup
from app.models.deposit_access import (
    DepositAccess,
    DepositAccessLevel,
)
from app.models.group_member import GroupMember
from app.models.role import Role
from app.models.user import User

from app.models.deposit import Deposit

ACCESS_LEVEL_ORDER = {
    DepositAccessLevel.VIEW: 1,
    DepositAccessLevel.EDIT: 2,
    DepositAccessLevel.ADMIN: 3,
}


def is_global_admin(
    db: Session,
    user: User,
) -> bool:

    statement = (
        select(Role.id)
        .join(User.roles)
        .where(
            User.id == user.id,
            Role.name == "administrator",
        )
    )

    return db.scalar(statement) is not None

def get_group_deposit_access_level(
    db: Session,
    user: User,
    deposit_id: int,
) -> DepositAccessLevel | None:

    if is_global_admin(db, user):

        return DepositAccessLevel.ADMIN

    statement = (
        select(DepositAccess.access_level)
        .join(
            GroupMember,
            GroupMember.group_id
            == DepositAccess.group_id,
        )
        .join(
            AccessGroup,
            AccessGroup.id
            == GroupMember.group_id,
        )
        .where(
            GroupMember.user_id == user.id,
            DepositAccess.deposit_id == deposit_id,
            AccessGroup.is_active.is_(True),
        )
    )

    access_levels = list(
        db.scalars(statement)
    )

    if not access_levels:

        return None

    return max(
        access_levels,
        key=lambda level: ACCESS_LEVEL_ORDER[level],
    )

def get_deposit_access_level(
    db: Session,
    user: User,
    deposit: Deposit,
) -> DepositAccessLevel | None:

    # Global administrators have unrestricted access.
    if is_global_admin(db, user):

        return DepositAccessLevel.ADMIN

    # Public deposits can be viewed by any
    # authenticated user.
    if deposit.visibility == "public":

        return DepositAccessLevel.VIEW

    # Group and private deposits require
    # explicit group access.
    return get_group_deposit_access_level(
        db,
        user,
        deposit.id,
    )

def can_view_deposit(
    db: Session,
    user: User,
    deposit_id: int,
) -> bool:

    access_level = get_deposit_access_level(
        db,
        user,
        deposit_id,
    )

    return access_level in {
        DepositAccessLevel.VIEW,
        DepositAccessLevel.EDIT,
        DepositAccessLevel.ADMIN,
    }

def can_edit_deposit(
    db: Session,
    user: User,
    deposit: Deposit,
) -> bool:

    if is_global_admin(db, user):

        return True

    if deposit.created_by == user.id:

        return True

    access_level = get_deposit_access_level(
        db,
        user,
        deposit,
    )

    return access_level in {
        DepositAccessLevel.EDIT,
        DepositAccessLevel.ADMIN,
    }

def can_administer_deposit(
    db: Session,
    user: User,
    deposit_id: int,
) -> bool:

    access_level = get_deposit_access_level(
        db,
        user,
        deposit_id,
    )

    return access_level == DepositAccessLevel.ADMIN




