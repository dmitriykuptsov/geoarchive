from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_db,
    require_admin,
)

from app.core.utils import count_active_admins

from app.core.security import hash_password

from app.models.role import Role
from app.models.user import User

from app.schemas.user import (
    UserCreateRequest,
    UserResponse,
    UserListResponse,
    UserUpdateRequest,
)

router = APIRouter()


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    request: UserCreateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> UserResponse:

    existing_user = db.scalar(select(User).where(User.username == request.username))

    if existing_user:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    if request.email:

        existing_email = db.scalar(select(User).where(User.email == request.email))

        if existing_email:

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )

    roles = list(db.scalars(select(Role).where(Role.id.in_(request.role_ids))))

    if len(roles) != len(set(request.role_ids)):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more roles do not exist",
        )

    user = User(
        username=request.username,
        email=request.email,
        password_hash=hash_password(request.password),
        is_active=True,
        must_change_password=True,
    )

    user.roles.extend(roles)

    db.add(user)

    try:

        db.commit()

        db.refresh(user)

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    return user


@router.get(
    "",
    response_model=UserListResponse,
)
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> UserListResponse:

    users = list(db.scalars(select(User).order_by(User.id)))

    return UserListResponse(
        items=users,
        total=len(users),
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> UserResponse:

    user = db.scalar(select(User).where(User.id == user_id))

    if user is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user(
    user_id: int,
    request: UserUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> UserResponse:

    user = db.scalar(select(User).where(User.id == user_id))

    if user is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if request.email is not None:

        existing_email = db.scalar(
            select(User).where(
                User.email == request.email,
                User.id != user_id,
            )
        )

        if existing_email:

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )

        user.email = request.email

    if request.is_active is not None:

        user.is_active = request.is_active

    if request.role_ids is not None:

        roles = list(db.scalars(select(Role).where(Role.id.in_(request.role_ids))))

        if len(roles) != len(set(request.role_ids)):

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more roles do not exist",
            )

        if (
            sum([1 if "administrator" == role.name else 0 for role in roles]) == 0
            and sum([1 if "administrator" == role.name else 0 for role in user.roles])
            != 0
            and count_active_admins(db) <= 1
        ):

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=("Cannot remove the last active administrator"),
            )

        user.roles = roles

    db.commit()

    db.refresh(user)

    return user
