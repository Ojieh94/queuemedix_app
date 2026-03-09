from pathlib import Path
from typing import Iterable, Union

from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType
from src.app.core.settings import Config


BASE_DIR = Path(__file__).resolve().parent

email_config = ConnectionConfig(
    MAIL_USERNAME=Config.EMAIL_USERNAME,
    MAIL_PASSWORD=Config.EMAIL_PASSWORD,
    MAIL_PORT=Config.EMAIL_PORT,
    MAIL_SERVER=Config.EMAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    MAIL_FROM=Config.EMAIL_FROM,
    MAIL_FROM_NAME=Config.MAIL_FROM_NAME,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False,
    # TEMPLATE_FOLDER = Path(BASE_DIR, "templates")
)


mail = FastMail(config=email_config)


def _normalize_recipients(recipients: Union[str, Iterable[Union[str, int]]]) -> list[str]:
    """Normalize recipients to a flat list of strings.

    FastAPI-Mail's MessageSchema expects a list of strings. Celery can
    sometimes deserialize task arguments into nested lists (e.g. `[['a@b.com']]`).
    This helper flattens a single nesting level and coerces values to strings.
    """

    if isinstance(recipients, str):
        return [recipients]

    if not isinstance(recipients, Iterable):
        return [str(recipients)]

    normalized: list[str] = []
    for r in recipients:
        if r is None:
            continue
        if isinstance(r, (list, tuple, set)):
            for inner in r:
                if inner is None:
                    continue
                normalized.append(str(inner))
        else:
            normalized.append(str(r))

    return normalized


def create_message(recipients: Union[str, list[str]], subject: str, body: str):
    recipients_norm = _normalize_recipients(recipients)

    message = MessageSchema(
        recipients=recipients_norm,
        subject=subject,
        body=body,
        subtype=MessageType.html
    )

    return message
