from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.user import User
from app.models.role import Role

from app.services.deposit_access import (
    can_administer_deposit, 
    can_edit_deposit, 
    can_view_deposit
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)


def get_db() -> Generator[Session, None, None]:

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    try:

        payload = decode_access_token(token)

        subject = payload.get("sub")

        if subject is None:
            raise credentials_exception

        user_id = int(subject)

    except (
        InvalidTokenError,
        ValueError,
        TypeError,
    ):

        raise credentials_exception

    user = db.scalar(
        select(User).where(
            User.id == user_id
        )
    )

    if user is None:
        raise credentials_exception

    if not user.is_active:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user

def require_admin(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> User:

    is_admin = db.scalar(
        select(Role.id)
        .join(User.roles)
        .where(
            User.id == current_user.id,
            Role.name == "administrator",
        )
    )

    if is_admin is None:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )

    return current_user

def require_password_changed(
    current_user: User = Depends(
        get_current_user
    ),
) -> User:

    if current_user.must_change_password:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password change required",
        )

    return current_user

def require_deposit_view_access(
    db: Session,
    user: User,
    deposit_id: int,
) -> None:

    if not can_view_deposit(
        db,
        user,
        deposit_id,
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this deposit",
        )
    

def require_deposit_edit_access(
    db: Session,
    user: User,
    deposit_id: int,
) -> None:

    if not can_edit_deposit(
        db,
        user,
        deposit_id,
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Edit access required",
        )


def require_global_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
) -> User:

    statement = (
        select(Role.id)
        .join(User.roles)
        .where(
            User.id == current_user.id,
            Role.name == "administrator",
        )
    )

    is_admin = db.scalar(statement) is not None

    if not is_admin:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )

    return current_user
