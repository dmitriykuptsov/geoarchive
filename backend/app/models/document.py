from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Enum,
    ForeignKey,
    String,
    Text,
    DateTime,
    Index,
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
    DocumentType,
    DocumentStatus,
    ExtractionMethod,
)

from sqlalchemy.dialects.mysql import BIGINT

if TYPE_CHECKING:

    from app.models.deposit import Deposit
    from app.models.user import User


class Document(
    UUIDMixin,
    TimestampMixin,
    Base,
):

    __tablename__ = "documents"

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

    uploaded_by: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "users.id",
        ),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    filename: Mapped[str] = mapped_column(
        String(500),
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

    storage_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType),
        nullable=False,
    )

    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus),
        nullable=False,
        default=DocumentStatus.UPLOADED,
    )

    checksum: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    processing_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    processing_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    deposit: Mapped["Deposit"] = relationship(
        back_populates="documents",
    )

    uploader: Mapped["User"] = relationship(
        back_populates="uploaded_documents",
    )

    pages: Mapped[list["DocumentPage"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )

class DocumentPage(Base):

    __tablename__ = "document_pages"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    document_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    page_number: Mapped[int] = mapped_column(
        nullable=False,
    )

    image_path: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    width: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    height: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    document: Mapped["Document"] = relationship(
        back_populates="pages",
    )

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="page",
        cascade="all, delete-orphan",
    )

class DocumentChunk(Base):

    __tablename__ = "document_chunks"

    __table_args__ = (
        Index(
            "ft_document_chunks_content",
            "content",
            mysql_prefix="FULLTEXT",
        ),
    )

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    document_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    page_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "document_pages.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    start_position: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    end_position: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    extraction_method: Mapped[ExtractionMethod] = mapped_column(
        Enum(ExtractionMethod),
        nullable=False,
    )

    document: Mapped["Document"] = relationship(
        back_populates="chunks",
    )

    page: Mapped["DocumentPage | None"] = relationship(
        back_populates="chunks",
    )


