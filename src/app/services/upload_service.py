import cloudinary.uploader

from fastapi import UploadFile

import cloudinary

from src.app.core.settings import Config

cloudinary.config(
    cloud_name=Config.CLOUDINARY_CLOUD_NAME,
    api_key=Config.CLOUDINARY_API_KEY,
    api_secret=Config.CLOUDINARY_API_SECRET,
    secure=True,
)


# print("Cloud Name:", Config.CLOUDINARY_CLOUD_NAME)
# print("API Key:", Config.CLOUDINARY_API_KEY)
# print("API Secret:", "***" if Config.CLOUDINARY_API_SECRET else None)


async def upload_profile_picture(
    file: UploadFile,
):
    result = cloudinary.uploader.upload(
        file.file,
        folder="queuemedix/profile_pictures",
    )

    return result["secure_url"]


async def upload_cover_image(
    file: UploadFile,
):
    result = cloudinary.uploader.upload(
        file.file,
        folder="queuemedix/hospital_cover-images",
    )

    return result["secure_url"]


async def upload_hospital_media(file: UploadFile, folder: str):

    result = cloudinary.uploader.upload(
        file.file,
        folder=folder
    )

    return {
        "url": result["secure_url"],
        "public_id": result["public_id"],
        "width": result["width"],
        "height": result["height"],
        "bytes": result["bytes"]
    }