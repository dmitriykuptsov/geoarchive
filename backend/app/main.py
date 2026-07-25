from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.deposits import router as deposits_router


app = FastAPI(
    title="GeoArchive API",
)


app.include_router(
    auth_router,
    prefix="/api/auth",
    tags=["Authentication"],
)

app.include_router(
    users_router,
    prefix="/api/users",
    tags=["Users"],
)

app.include_router(
    deposits_router,
    prefix="/api/deposits",
    tags=["Deposits"],
)

