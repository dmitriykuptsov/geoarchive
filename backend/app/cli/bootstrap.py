import getpass

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User


DEFAULT_ROLES = (
    "administrator",
    "geologist",
    "buyer",
)


def create_roles(session) -> dict[str, Role]:

    roles: dict[str, Role] = {}

    for role_name in DEFAULT_ROLES:

        role = session.scalar(
            select(Role).where(
                Role.name == role_name
            )
        )

        if role is None:

            role = Role(
                name=role_name,
            )

            session.add(role)
            session.flush()

            print(
                f"Created role: {role_name}"
            )

        else:

            print(
                f"Role already exists: {role_name}"
            )

        roles[role_name] = role

    return roles


def create_admin(
    session,
    admin_role: Role,
) -> None:

    admin_exists = session.scalar(
        select(User)
        .join(User.roles)
        .where(
            Role.name == "administrator"
        )
    )

    if admin_exists:

        print(
            "Administrator already exists:"
            f" {admin_exists.username}"
        )

        return

    print()
    print("Creating initial administrator")

    username = input(
        "Username: "
    ).strip()

    email = input(
        "Email: "
    ).strip()

    password = getpass.getpass(
        "Password: "
    )

    password_confirmation = getpass.getpass(
        "Confirm password: "
    )

    if password != password_confirmation:

        raise ValueError(
            "Passwords do not match"
        )

    if not username:

        raise ValueError(
            "Username cannot be empty"
        )

    if not password:

        raise ValueError(
            "Password cannot be empty"
        )

    user = User(
        username=username,
        email=email or None,
        password_hash=hash_password(password),
        is_active=True,
        must_change_password=False,
    )

    user.roles.append(admin_role)

    session.add(user)

    print(
        f"Administrator '{username}' "
        "created successfully"
    )


def bootstrap() -> None:

    with SessionLocal() as session:

        try:

            roles = create_roles(session)

            create_admin(
                session,
                roles["administrator"],
            )

            session.commit()

            print()
            print(
                "Bootstrap completed successfully."
            )

        except Exception:

            session.rollback()

            raise