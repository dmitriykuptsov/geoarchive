from pathlib import Path

from fastapi.responses import FileResponse

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    File,
    Form,
    UploadFile,
)

from enum import Enum as PyEnum

from sqlalchemy import select
from sqlalchemy.orm import Session

from pathlib import Path
from uuid import uuid4

from app.core.dependencies import (
    get_current_user,
    get_db,
    require_password_changed,
    require_global_admin    
)

from app.services.document_storage import DocumentStorage, document_storage

from app.models.deposit import Deposit
from app.models.user import User
from app.models.access_group import AccessGroup
from app.models.group_member import (
    GroupMember
)

from app.models.deposit_access import (
    DepositAccess,
    DepositAccessLevel
)

from app.models.document import Document, DocumentStatus, DocumentType

from app.services.deposit_access import (
    can_view_deposit,
    can_edit_deposit,
    can_administer_deposit,
    is_global_admin
)

from app.schemas.document import DocumentResponse

router = APIRouter()

@router.get(
    "/{document_id}/download",
)
def download_document(
    document_id: int,

    db: Session = Depends(
        get_db,
    ),

    current_user: User = Depends(
        require_password_changed,
    ),
):

    document = db.scalar(
        select(
            Document,
        ).where(
            Document.id
            == document_id,
        )
    )

    if document is None:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),

            detail=(
                "Document not found"
            ),
        )

    has_access = db.scalar(
        select(
            DepositAccess.id,
        )
        .join(
            GroupMember,

            GroupMember.group_id
            == DepositAccess.group_id,
        )
        .where(

            DepositAccess.deposit_id
            == document.deposit_id,

            GroupMember.user_id
            == current_user.id,
        )
    )

    if has_access is None and \
        not is_global_admin(
            db=db, 
            user=current_user
        ):

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),

            detail=(
                "Access to this deposit "
                "is required"
            ),
        )

    file_path = (
        document_storage.base_path
        / document.storage_path
    )

    if not file_path.exists():

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),

            detail=(
                "Document file not found"
            ),
        )

    return FileResponse(
        path=file_path,

        media_type=(
            document.mime_type
        ),

        filename=(
            document.filename
        ),
    )

@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
) -> None:

    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
        )
    )

    if document is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    has_admin_access = db.scalar(
        select(DepositAccess.id)
        .join(
            GroupMember,
            GroupMember.group_id
            == DepositAccess.group_id,
        )
        .where(
            DepositAccess.deposit_id
            == document.deposit_id,

            GroupMember.user_id
            == current_user.id,

            DepositAccess.access_level
            == DepositAccessLevel.ADMIN,
        )
    )

    if has_admin_access is None and \
        not is_global_admin(
            db=db, 
            user=current_user
        ):
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "ADMIN access to this deposit "
                "is required"
            ),
        )

    storage_path = document.storage_path

    document_storage.delete(
        storage_path,
    )

    db.delete(
        document,
    )

    db.commit()