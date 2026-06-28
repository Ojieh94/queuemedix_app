import cloudinary

from src.app.core.settings import Config

cloudinary.config(
    cloud_name=Config.CLOUDINARY_CLOUD_NAME,
    api_key=Config.CLOUDINARY_API_KEY,
    api_secret=Config.CLOUDINARY_API_SECRET,
    secure=True,
)


print("Cloud Name:", Config.CLOUDINARY_CLOUD_NAME)
print("API Key:", Config.CLOUDINARY_API_KEY)
print("API Secret:", "***" if Config.CLOUDINARY_API_SECRET else None)