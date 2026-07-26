from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    app_name: str = "GeoArchive"

    jwt_secret_key: str

    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = 60

    database_url: str = Field(validation_alias="DATABASE_URL")

    document_storage_path: str = (
        "./storage"
    )

    redis_url: str = (
        "redis://redis:6379/0"
    )

    celery_broker_url: str = (
        "redis://redis:6379/0"
    )

    celery_result_backend: str = (
        "redis://redis:6379/1"
    )

    class Config:

        env_file = ".env"


settings = Settings()
