from typing import List

from sqlalchemy import (
    ForeignKey,
    String,
    Table,
    Column,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import (
    Base,
    UUIDMixin,
)

from sqlalchemy.dialects.mysql import BIGINT


class Role(
    UUIDMixin,
    Base,
):

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    users: Mapped[List["User"]] = relationship(
        secondary="user_roles",
        back_populates="roles",
    )


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        BIGINT(unsigned=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
    Column(
        "role_id",
        BIGINT(unsigned=True),
        ForeignKey(
            "roles.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)
