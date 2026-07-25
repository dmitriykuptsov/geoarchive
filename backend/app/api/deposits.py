from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from enum import Enum as PyEnum

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_user,
    get_db,
    require_password_changed,
)

from app.models.deposit import Deposit
from app.models.user import User

from app.services.deposit_access import (
    can_view_deposit,
    can_edit_deposit,
    can_administer_deposit
)

from app.schemas.deposit import (
    DepositCreateRequest,
    DepositResponse,
    DepositUpdateRequest,
)


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