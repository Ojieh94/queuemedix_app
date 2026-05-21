import cloudinary.uploader

from fastapi import UploadFile


async def upload_profile_picture(
    file: UploadFile,
):
    result = cloudinary.uploader.upload(
        file.file,
        folder="queuemedix/profile_pictures",
    )

    return result["secure_url"]