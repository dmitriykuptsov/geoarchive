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

from app.schemas.deposit import (
    DepositCreateRequest,
    DepositResponse,
    DepositUpdateRequest,
)

from app.schemas.deposit_access import (
    DepositAccessCreateRequest,
    DepositAccessResponse,
)

from app.schemas.document import DocumentResponse

router = APIRouter()

@router.get(
    "/{deposit_id}",
    response_model=DepositResponse,
)
def get_deposit(
    deposit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed
    ),
) -> Deposit:

    deposit = db.scalar(
        select(Deposit).where(
            Deposit.id == deposit_id
        )
    )

    if deposit is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deposit not found",
        )

    if not can_view_deposit(
        db,
        current_user,
        deposit,
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have access "
                "to this deposit"
            ),
        )

    return deposit

@router.post(
    "",
    response_model=DepositResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_deposit(
    request: DepositCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed
    ),
) -> Deposit:

    existing_deposit = db.scalar(
        select(Deposit).where(
            Deposit.name == request.name,
        )
    )

    if existing_deposit is not None:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A deposit with this name "
                "already exists"
            ),
        )

    deposit = Deposit(
        name=request.name,
        description=request.description,
        country=request.country,
        region=request.region,
        status=request.status.value,
        visibility=request.visibility.value,
        created_by=current_user.id,
        latitude=request.latitude,
        longitude=request.longitude
    )

    db.add(deposit)

    db.commit()

    db.refresh(deposit)

    return deposit

@router.patch(
    "/{deposit_id}",
    response_model=DepositResponse,
)
def update_deposit(
    deposit_id: int,
    request: DepositUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed
    ),
) -> Deposit:


    deposit = db.scalar(
            select(Deposit).where(
                Deposit.id == deposit_id
            )
        )
    
    if deposit is None:
    
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deposit not found",
        )
    
    if (
        request.visibility is not None
        and not can_administer_deposit(
            db,
            current_user,
            deposit,
        )
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Deposit administrator access "
                "is required to change visibility"
            ),
        )

    

    if not can_edit_deposit(
        db,
        current_user,
        deposit,
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Edit access required"
            ),
        )

    if request.name is not None:

        existing_deposit = db.scalar(
            select(Deposit).where(
                Deposit.name == request.name,
                Deposit.id != deposit_id,
            )
        )

        if existing_deposit is not None:

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A deposit with this name "
                    "already exists"
                ),
            )

    update_data = request.model_dump(
        exclude_unset=True,
    )

    for field, value in update_data.items():

        if isinstance(value, PyEnum):

            value = value.value

        setattr(
            deposit,
            field,
            value,
        )

    db.commit()

    db.refresh(deposit)

    return deposit


@router.post(
    "/{deposit_id}/access-groups",
    response_model=DepositAccessResponse,
    status_code=status.HTTP_201_CREATED,
)
def grant_deposit_access(
    deposit_id: int,
    request: DepositAccessCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
) -> DepositAccess:

    deposit = db.scalar(
        select(Deposit).where(
            Deposit.id == deposit_id,
        )
    )

    if deposit is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deposit not found",
        )

    # Check that the current user has ADMIN access
    # to this deposit.
    has_admin_access = db.scalar(
        select(DepositAccess.id)
        .join(
            GroupMember,
            GroupMember.group_id
            == DepositAccess.group_id,
        )
        .where(
            DepositAccess.deposit_id
            == deposit_id,

            GroupMember.user_id
            == current_user.id,

            DepositAccess.access_level
            == DepositAccessLevel.ADMIN,
        )
    )

    if has_admin_access is None and \
        not is_global_admin(
            db = db, 
            user = current_user
        ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Administrator access to this deposit "
                "is required"
            ),
        )

    group = db.scalar(
        select(AccessGroup).where(
            AccessGroup.id == request.group_id,
            AccessGroup.is_active.is_(True),
        )
    )

    if group is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access group not found",
        )

    existing_access = db.scalar(
        select(DepositAccess).where(
            DepositAccess.deposit_id == deposit_id,
            DepositAccess.group_id
            == request.group_id,
        )
    )

    if existing_access is not None:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This group already has access "
                "to this deposit"
            ),
        )

    access = DepositAccess(
        deposit_id=deposit_id,
        group_id=request.group_id,
        access_level=request.access_level,
    )

    db.add(access)
    db.commit()
    db.refresh(access)

    return access


@router.delete(
    "/{deposit_id}/access-groups/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def revoke_deposit_access(
    deposit_id: int,
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
) -> None:

    access = db.scalar(
        select(DepositAccess).where(
            DepositAccess.deposit_id == deposit_id,
            DepositAccess.group_id == group_id,
        )
    )

    if access is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deposit access rule not found",
        )

    has_admin_access = db.scalar(
        select(DepositAccess.id)
        .join(
            GroupMember,
            GroupMember.group_id
            == DepositAccess.group_id,
        )
        .where(
            DepositAccess.deposit_id == deposit_id,
            GroupMember.user_id == current_user.id,
            DepositAccess.access_level
            == DepositAccessLevel.ADMIN,
        )
    )

    if has_admin_access is None and \
        not is_global_admin(
            db = db, 
            user = current_user
        ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Administrator access to this deposit "
                "is required"
            ),
        )

    db.delete(access)
    db.commit()

@router.get(
    "/{deposit_id}/access-groups",
    response_model=list[DepositAccessResponse],
)
def list_deposit_access(
    deposit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
) -> list[DepositAccess]:

    deposit_exists = db.scalar(
        select(Deposit.id).where(
            Deposit.id == deposit_id,
        )
    )

    if deposit_exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deposit not found",
        )

    has_admin_access = db.scalar(
        select(DepositAccess.id)
        .join(
            GroupMember,
            GroupMember.group_id
            == DepositAccess.group_id,
        )
        .where(
            DepositAccess.deposit_id == deposit_id,
            GroupMember.user_id == current_user.id,
            DepositAccess.access_level
            == DepositAccessLevel.ADMIN,
        )
    )

    if has_admin_access is None and \
          not is_global_admin(
            db = db, 
            user = current_user
        ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Administrator access to this deposit "
                "is required"
            ),
        )

    return db.scalars(
        select(DepositAccess)
        .where(
            DepositAccess.deposit_id == deposit_id,
        )
        .order_by(
            DepositAccess.created_at,
        )
    ).all()

@router.post(
    "/{deposit_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    deposit_id: int,

    title: str = Form(...),

    document_type: DocumentType = Form(...),

    file: UploadFile = File(...),

    db: Session = Depends(
        get_db,
    ),

    current_user: User = Depends(
        require_password_changed,
    ),
) -> Document:

    deposit = db.scalar(
        select(
            Deposit,
        ).where(
            Deposit.id
            == deposit_id,
        )
    )

    if deposit is None:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),

            detail=(
                "Deposit not found"
            ),
        )

    has_edit_access = db.scalar(
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
            == deposit_id,

            GroupMember.user_id
            == current_user.id,

            DepositAccess.access_level.in_(
                [
                    DepositAccessLevel.EDIT,
                    DepositAccessLevel.ADMIN,
                ],
            ),
        )
    )

    if has_edit_access is None and\
        not is_global_admin(
            db = db, 
            user = current_user
        ):

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),

            detail=(
                "EDIT or ADMIN access "
                "is required"
            ),
        )

    if file.content_type != (
        "application/pdf"
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),

            detail=(
                "Only PDF files are supported"
            ),
        )

    if not file.filename:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),

            detail=(
                "Filename is required"
            ),
        )

    original_filename = (
        file.filename
    )

    storage_filename = (
        f"{uuid4()}.pdf"
    )

    (
        storage_path,

        file_size,

        checksum,

    ) = await document_storage.save(

        file=file,

        deposit_id=deposit_id,

        storage_filename=(
            storage_filename
        ),
    )

    document = Document(

        deposit_id=deposit_id,

        uploaded_by=current_user.id,

        title=title,

        filename=original_filename,

        mime_type=(
            file.content_type
        ),

        file_size=file_size,

        storage_path=storage_path,

        checksum=checksum,

        document_type=document_type,

        status=(
            DocumentStatus.UPLOADED
        ),
    )

    db.add(
        document,
    )

    db.commit()

    db.refresh(
        document,
    )

    return document