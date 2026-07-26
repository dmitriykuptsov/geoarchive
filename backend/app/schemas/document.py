from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import (
    DocumentStatus,
    DocumentType,
)


class DocumentResponse(BaseModel):

    id: int
    deposit_id: int
    uploaded_by: int

    title: str
    filename: str
    mime_type: str
    file_size: int
    storage_path: str

    document_type: DocumentType
    status: DocumentStatus

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )