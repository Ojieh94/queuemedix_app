from celery import Celery, Task
from src.app.core.email_utils import mail, create_message
from fastapi_mail.errors import ConnectionErrors
from asgiref.sync import async_to_sync

app = Celery()

app.config_from_object("src.app.core.settings")


# @app.task()
# def send_email_task(recipients:list[str], subject: str, body: str):
#     try:
#         message = create_message(
#             recipients=recipients,
#             subject=subject,
#             body=body
#         )

#         async_to_sync(mail.send_message)(message)
#         print("Message sent successfully!")
#         return "done"
    
#     except Exception as e:
#         print(f"Error sending email: {e}")
#         raise


class EmailTask(Task):
    autoretry_for = (ConnectionErrors,)
    # retry up to 3 times, wait 5s
    retry_kwargs = {'max_retries': 3, 'countdown': 5}
    retry_backoff = True  # exponential backoff
    retry_jitter = True   # add random jitter to avoid thundering herd


@app.task(base=EmailTask, bind=True)
def send_email_task(self, recipients: list[str], subject: str, body: str):
    try:
        message = create_message(
            recipients=recipients,
            subject=subject,
            body=body
                )

        # async_to_sync because FastMail is async
        async_to_sync(mail.send_message)(message)
        print(f"✅ Message sent successfully to: {recipients}")
    except ConnectionErrors as e:
        print(f"⚠️ Connection error, retrying... {e}")
        raise self.retry(exc=e)
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        raise self.retry(exc=e)
