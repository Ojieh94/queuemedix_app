from src.app.core.settings import Config
from src.app.core import celery

def send_verification_email(email: str, token: str):
    """
    Builds and sends a verification email to the given user.
    """
    link = f"http://{Config.DOMAIN}/api/v1/auth/email_verification/{token}"

    # HTML body
    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
            <h2 style="color: #333333;">Verify Your Email Address</h2>
            <p style="font-size: 16px; color: #555555;">
                Thank you for joining the family! Please click the button below to verify your account:
            </p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{link}" style="background-color: #4CAF50; color: white; padding: 14px 25px; text-decoration: none; border-radius: 5px; display: inline-block;">
                Verify Email
                </a>
            </p>
            <p style="font-size: 14px; color: #888888;">
                If the button doesn't work, copy and paste the following link into your browser:
            </p>
            <p style="font-size: 14px; color: #888888; word-break: break-all;">
                {link}
            </p>
        </div>

        <div style="max-width: 600px; margin: auto; padding: 30px;">
        <p style="font-size: 14px; color: #888888;">
            Please do not reply to this email. It's an automated address.
        </p>
        </div>
    </body>
    </html>
    """

    subject = "Please Verify your email"

    email_list = [email]

    # Push email to Celery
    celery.send_email_task.delay(email_list, subject, body_html)


# Send password reset email

def send_password_reset_email(email: str, token: str):
    """
    Builds and sends a password reset email.
    """
    link = f"http://{Config.DOMAIN}/api/v1/auth/password-resets/{token}"

    # HTML body
    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
            <h2 style="color: #333333;">Password Reset</h2>
            <p style="font-size: 16px; color: #555555;">
                Hello there! Please click the button below to reset your password:
            </p>
            <p style="font-size: 14px; color: #888888;">
                PLEASE NOTE: This link expires in 5mins.
            </p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{link}" style="background-color: #4CAF50; color: white; padding: 14px 25px; text-decoration: none; border-radius: 5px; display: inline-block;">
                Password Reset
                </a>
            </p>
            <p style="font-size: 14px; color: #888888;">
                If the button doesn't work, copy and paste the following link into your browser:
            </p>
            <p style="font-size: 14px; color: #888888; word-break: break-all;">
                {link}
            </p>
        </div>

        <div style="max-width: 600px; margin: auto; padding: 30px;">
        <p style="font-size: 14px; color: #888888;">
            Please do not reply to this email. It's an automated address.
        </p>
        </div>
    </body>
    </html>
    """

    subject = "Password Reset"

    email_list = [email]

    # Push email to Celery
    celery.send_email_task.delay(email_list, subject, body_html)


def send_test(email: str,):
    """
    Sends a testing email.
    """
    link = f"https://www.google.com"

    # HTML body
    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
            <h2 style="color: #333333;">Testing Email</h2>
            <p style="font-size: 16px; color: #555555;">
                You've received this email for testing purpose. please ignore
            </p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{link}" style="background-color: #4CAF50; color: white; padding: 14px 25px; text-decoration: none; border-radius: 5px; display: inline-block;">
                GOOGLE
                </a>
            </p>
            <p style="font-size: 14px; color: #888888;">
                If the button doesn't work, copy and paste the following link into your browser:
            </p>
            <p style="font-size: 14px; color: #888888; word-break: break-all;">
                {link}
            </p>
        </div>

        <div style="max-width: 600px; margin: auto; padding: 30px;">
        <p style="font-size: 14px; color: #888888;">
            Please do not reply to this email. It's an automated address.
        </p>
        </div>
    </body>
    </html>
    """

    subject = "Hola!"

    email_list = [email]

    # Push email to Celery
    celery.send_email_task.delay(email_list, subject, body_html)
