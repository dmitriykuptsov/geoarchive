from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Integer,
    Numeric,
    DateTime
)

from sqlalchemy import select, func

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

from app.models.enums import (
    MapType,
    MapFileType,
)

from decimal import Decimal
from datetime import datetime
from sqlalchemy.dialects.mysql import BIGINT

class Contour(Base):
    __tablename__ = "contours"

    __table_args__ = (
        UniqueConstraint(
            "map_id",
            "name",
            name="uq_contour_map_name",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    map_id: Mapped[int] = mapped_column(
        ForeignKey(
            "maps.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    map: Mapped["Map"] = relationship(
        "Map",
        back_populates="contours",
    )

    points: Mapped[list["ContourPoint"]] = relationship(
        "ContourPoint",
        back_populates="contour",
        cascade="all, delete-orphan",
        order_by="ContourPoint.sequence",
    )

class ContourPoint(Base):
    __tablename__ = "contour_points"

    __table_args__ = (
        UniqueConstraint(
            "contour_id",
            "sequence",
            name="uq_contour_point_sequence",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    contour_id: Mapped[int] = mapped_column(
        ForeignKey(
            "contours.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    pixel_x: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    pixel_y: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    longitude: Mapped[Decimal] = mapped_column(
        Numeric(12, 8),
        nullable=False,
    )

    latitude: Mapped[Decimal] = mapped_column(
        Numeric(11, 8),
        nullable=False,
    )

    contour: Mapped["Contour"] = relationship(
        "Contour",
        back_populates="points",
    )