from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType
from src.app.core.settings import Config
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

email_config = ConnectionConfig(
    MAIL_USERNAME=Config.EMAIL_USERNAME,
    MAIL_PASSWORD=Config.EMAIL_PASSWORD,
    MAIL_PORT= Config.EMAIL_PORT,
    MAIL_SERVER=Config.EMAIL_SERVER,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    MAIL_FROM=Config.EMAIL_FROM,
    MAIL_FROM_NAME=Config.MAIL_FROM_NAME,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS = True,
    TEMPLATE_FOLDER = Path(BASE_DIR, "templates")
)


mail = FastMail(config=email_config)

def create_message(recipients: list[str], subject: str, body: str):

    message = MessageSchema(
        recipients=recipients,
        subject=subject,
        body=body,
        subtype=MessageType.html
    )

    return message