from pathlib import Path
from uuid import UUID
from app.core.config import settings

import hashlib

from fastapi import UploadFile

class FileStorage:

    def __init__(
        self,
        base_path: str,
    ) -> None:

        self.base_path = Path(
            base_path,
        )


    async def save(
        self,
        file: UploadFile,
        category: str,
        deposit_id: int,
        storage_filename: str,
    ) -> tuple[str, int, str]:

        deposit_directory = (
            self.base_path
            / category
            / str(deposit_id)
        )

        deposit_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination = (
            deposit_directory
            / storage_filename
        )

        hasher = hashlib.sha256()

        file_size = 0

        with destination.open("wb") as output:

            while chunk := await file.read(
                1024 * 1024,
            ):

                output.write(chunk)

                hasher.update(chunk)

                file_size += len(chunk)

        await file.close()

        relative_path = destination.relative_to(
            self.base_path,
        )

        checksum = hasher.hexdigest()

        return (
            str(relative_path),
            file_size,
            checksum,
        )

    def delete(
        self,
        storage_path: str,
    ) -> None:

        file_path = (
            self.base_path
            / storage_path
        )

        if file_path.exists():

            file_path.unlink()

file_storage = FileStorage(
    base_path=settings.document_storage_path,
)