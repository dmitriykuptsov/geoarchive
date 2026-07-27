from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    Enum,
    ForeignKey,
    JSON,
    String,
    Text,
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
    LayerType,
    GeometryType,
)

from sqlalchemy.dialects.mysql import BIGINT

if TYPE_CHECKING:

    from app.models.deposit import Deposit
    from app.models.user import User


class Layer(
    UUIDMixin,
    TimestampMixin,
    Base,
):

    __tablename__ = "layers"

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

    layer_type: Mapped[LayerType] = mapped_column(
        Enum(LayerType),
        nullable=False,
    )

    geometry_type: Mapped[GeometryType] = mapped_column(
        Enum(GeometryType),
        nullable=False,
    )

    visible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    editable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_by: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "users.id",
        ),
        nullable=False,
    )

    features: Mapped[list["LayerFeature"]] = relationship(
        back_populates="layer",
        cascade="all, delete-orphan",
    )

    deposit: Mapped["Deposit"] = relationship(
        back_populates="layers",
    )


class LayerFeature(Base):

    __tablename__ = "layer_features"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    layer_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "layers.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    geometry: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    properties: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    layer: Mapped["Layer"] = relationship(
        back_populates="features",
    )
