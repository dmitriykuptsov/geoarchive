from celery import Task
from datetime import datetime, timezone

from app.worker.celery_app import celery_app

from app.core.database import SessionLocal
from app.models.document import Document, DocumentStatus, DocumentPage, DocumentChunk
from app.services.pdf_processor import PDFProcessor
from app.services.text_chunker import TextChunker
from app.services.document_storage import DocumentStorage, document_storage
from app.models.enums import ExtractionMethod

@celery_app.task(
    name="documents.process",
)
def process_document(
    document_id: int,
) -> dict:

    db = SessionLocal()

    try:

        document = db.get(
            Document,
            document_id,
        )

        if document is None:

            raise ValueError(
                "Document not found"
            )

        document.status = (
            DocumentStatus.PROCESSING
        )

        document.processing_started_at = (
            datetime.now(
                timezone.utc,
            )
        )

        document.processing_completed_at = None

        document.processing_error = None

        db.commit()

        processor = PDFProcessor()

        file_path = (
            document_storage.base_path
            / document.storage_path
        )

        pages = processor.extract(
            str(file_path),
        )

        chunker = TextChunker()

        for page_data in pages:

            page = DocumentPage(
                document_id=document.id,

                page_number=(
                    page_data[
                        "page_number"
                    ]
                ),

                width=(
                    page_data[
                        "width"
                    ]
                ),

                height=(
                    page_data[
                        "height"
                    ]
                ),
            )

            db.add(page)

            db.flush()

            chunks = chunker.split(
                page_data["text"],
            )

            for chunk_index, content in enumerate(
                chunks,
            ):

                chunk = DocumentChunk(
                    document_id=document.id,

                    page_id=page.id,

                    chunk_index=chunk_index,

                    content=content,

                    extraction_method = ExtractionMethod.NATIVE_PDF
                )

                db.add(chunk)

        document.status = (
            DocumentStatus.PROCESSED
        )

        document.processing_completed_at = (
            datetime.now(
                timezone.utc,
            )
        )

        document.processing_error = None

        db.commit()

        return {
            "document_id": document.id,

            "status": "processed",

            "pages": len(pages),
        }

    except Exception:

        db.rollback()

        document = db.get(
            Document,
            document_id,
        )

        if document is not None:

            document.status = (
                DocumentStatus.FAILED
            )

            document.processing_error = str(
                exc
            )

            document.processing_completed_at = (
                datetime.now(
                    timezone.utc,
                )
            )

            db.commit()

        raise

    finally:
        
        db.close()
