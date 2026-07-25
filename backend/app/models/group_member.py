from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    UniqueConstraint,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import (
    Base,
    TimestampMixin,
)

from sqlalchemy.dialects.mysql import BIGINT

if TYPE_CHECKING:

    from app.models.user import User
    from app.models.access_group import AccessGroup


class GroupMember(
    TimestampMixin,
    Base,
):

    __tablename__ = "group_members"

    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "user_id",
            name="uq_group_member",
        ),
    )

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    group_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "access_groups.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    group: Mapped["AccessGroup"] = relationship(
        back_populates="members",
    )

    user: Mapped["User"] = relationship()
