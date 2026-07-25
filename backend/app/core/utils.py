from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.role import Role

def count_active_admins(
    db: Session,
) -> int:

    return db.scalar(
        select(func.count(User.id))
        .join(User.roles)
        .where(
            User.is_active.is_(True),
            Role.name == "administrator",
        )
    ) or 0