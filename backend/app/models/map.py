from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
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

from sqlalchemy.dialects.mysql import BIGINT

if TYPE_CHECKING:

    from app.models.deposit import Deposit
    from app.models.user import User


class Map(
    UUIDMixin,
    TimestampMixin,
    Base,
):

    __tablename__ = "maps"

    __table_args__ = (
        UniqueConstraint(
            "deposit_id",
            "name",
            name="uq_map_deposit_name",
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
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    map_type: Mapped[MapType] = mapped_column(
        Enum(MapType),
        nullable=False,
    )

    coordinate_system: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="EPSG:4326",
    )

    created_by: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "users.id",
        ),
        nullable=False,
    )

    deposit: Mapped["Deposit"] = relationship(
        back_populates="maps",
    )

    files: Mapped[list["MapFile"]] = relationship(
        back_populates="map",
        cascade="all, delete-orphan",
    )

    calibration_points: Mapped[list["MapCalibrationPoint"]] = relationship(
        back_populates="map",
        cascade="all, delete-orphan",
    )


class MapFile(Base):

    __tablename__ = "map_files"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    map_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "maps.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    file_type: Mapped[MapFileType] = mapped_column(
        Enum(MapFileType),
        nullable=False,
    )

    storage_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    width: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    height: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    map: Mapped["Map"] = relationship(
        back_populates="files",
    )


class MapCalibrationPoint(Base):

    __tablename__ = "map_calibration_points"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    map_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "maps.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    pixel_x: Mapped[float] = mapped_column(
        nullable=False,
    )

    pixel_y: Mapped[float] = mapped_column(
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        nullable=False,
    )

    latitude: Mapped[float] = mapped_column(
        nullable=False,
    )

    map: Mapped["Map"] = relationship(
        back_populates="calibration_points",
    )
