from celery import Celery
from src.app.core.email_utils import mail, create_message
from asgiref.sync import async_to_sync

app = Celery()

app.config_from_object("src.app.core.settings")

@app.task()
def send_email_task(recipients:list[str], subject: str, body: str):
    try:
        message = create_message(
            recipients=recipients,
            subject=subject,
            body=body
        )

        async_to_sync(mail.send_message)(message)
        print("Message sent successfully!")
        return "done"
    
    except Exception as e:
        print(f"Error sending email: {e}")
        raise