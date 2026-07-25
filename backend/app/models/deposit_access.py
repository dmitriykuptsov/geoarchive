from typing import TYPE_CHECKING

from enum import Enum as PyEnum

from sqlalchemy import (
    BigInteger,
    Enum,
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

    from app.models.access_group import AccessGroup
    from app.models.deposit import Deposit


class DepositAccessLevel(str, PyEnum):

    VIEW = "view"

    EDIT = "edit"

    ADMIN = "admin"


class DepositAccess(
    TimestampMixin,
    Base,
):

    __tablename__ = "deposit_access"

    __table_args__ = (
        UniqueConstraint(
            "deposit_id",
            "group_id",
            name="uq_deposit_group_access",
        ),
    )

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    deposit_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "deposits.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    group_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "access_groups.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    access_level: Mapped[DepositAccessLevel] = mapped_column(
        Enum(DepositAccessLevel),
        nullable=False,
        default=DepositAccessLevel.VIEW,
    )

    deposit: Mapped["Deposit"] = relationship(
        back_populates="access_rules",
    )

    group: Mapped["AccessGroup"] = relationship(
        back_populates="deposit_access",
    )
