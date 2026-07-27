from typing import List

from datetime import date

from sqlalchemy import Boolean, Date, DECIMAL, ForeignKey, Integer, Text, Enum, String

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)


from app.models.base import Base, UUIDMixin

from sqlalchemy.dialects.mysql import BIGINT


class AttributeDefinition(
    UUIDMixin,
    Base,
):

    __tablename__ = "attribute_definitions"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    data_type: Mapped[str] = mapped_column(
        Enum(
            "text",
            "integer",
            "decimal",
            "boolean",
            "date",
        ),
        nullable=False,
    )

    unit: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    values: Mapped[List["DepositAttribute"]] = relationship(
        back_populates="definition",
    )


class DepositAttribute(Base):

    __tablename__ = "deposit_attributes"

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

    attribute_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "attribute_definitions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    value_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    value_integer: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    value_decimal: Mapped[float | None] = mapped_column(
        DECIMAL(
            30,
            10,
        ),
        nullable=True,
    )

    value_boolean: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    value_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    deposit: Mapped["Deposit"] = relationship(
        back_populates="attributes",
    )

    definition: Mapped["AttributeDefinition"] = relationship(
        back_populates="values",
    )
