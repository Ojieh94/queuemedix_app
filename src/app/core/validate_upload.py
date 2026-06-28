from fastapi import UploadFile

from src.app.core import errors


async def validate_upload(
    file: UploadFile,
    *,
    allowed_types: set[str],
    max_size: int,
):
    if file.content_type not in allowed_types:
        raise errors.InvalidFileType()

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size > max_size:
        raise errors.FileTooLarge()