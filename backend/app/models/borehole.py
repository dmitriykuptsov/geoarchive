from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Integer,
    Numeric
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

from app.models.enums import (
    MapType,
    MapFileType,
)

from decimal import Decimal
from sqlalchemy.dialects.mysql import BIGINT

if TYPE_CHECKING:

    from app.models.deposit import Deposit
    from app.models.user import User

class Borehole(
    UUIDMixin,
    TimestampMixin,
    Base
    ):
    
    __tablename__ = "boreholes"

    __table_args__ = (
        UniqueConstraint(
            "map_id",
            "name",
            name="uq_borehole_map_name",
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

    map: Mapped["Map"] = relationship(
        "Map",
        back_populates="boreholes",
    )