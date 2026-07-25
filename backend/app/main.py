from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.users import router as users_router

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

