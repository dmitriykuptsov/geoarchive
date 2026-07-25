from typing import List

from sqlalchemy import Boolean, String
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from sqlalchemy.dialects.mysql import BIGINT

from app.models.base import (
    Base,
    UUIDMixin,
    TimestampMixin,
)

class User(
    UUIDMixin,
    TimestampMixin,
    Base,
):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    first_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    last_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    roles: Mapped[List["Role"]] = relationship(
        secondary="user_roles",
        back_populates="users",
    )

    deposits: Mapped[List["Deposit"]] = relationship(
        back_populates="creator",
    )

    groups: Mapped[list["GroupMember"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
