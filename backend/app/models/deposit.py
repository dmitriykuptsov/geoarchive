from typing import List

from sqlalchemy import (
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    ForeignKey,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import (
    Base,
    UUIDMixin,
    TimestampMixin,
)

from sqlalchemy.dialects.mysql import BIGINT

class Deposit(
    UUIDMixin,
    TimestampMixin,
    Base,
):

    __tablename__ = "deposits"

    __table_args__ = (
        UniqueConstraint(
            "name",
            name="uq_deposits_name",
        ),
    )

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    region: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "active",
            "inactive",
            "archived",
        ),
        nullable=False,
        default="active",
    )

    visibility: Mapped[str] = mapped_column(
        Enum(
            "private",
            "group",
            "public",
        ),
        nullable=False,
        default="private",
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
        ),
        nullable=False,
    )

    creator: Mapped["User"] = relationship(
        back_populates="deposits",
    )

    attributes: Mapped[List["DepositAttribute"]] = relationship(
        back_populates="deposit",
        cascade="all, delete-orphan",
    )

    documents: Mapped[list["Document"]] = relationship(
        back_populates="deposit",
        cascade="all, delete-orphan",
    )

    maps: Mapped[list["Map"]] = relationship(
        back_populates="deposit",
        cascade="all, delete-orphan",
    )

    layers: Mapped[list["Layer"]] = relationship(
        back_populates="deposit",
        cascade="all, delete-orphan",
    )

    access_rules: Mapped[list["DepositAccess"]] = relationship(
        back_populates="deposit",
        cascade="all, delete-orphan",
    )

    