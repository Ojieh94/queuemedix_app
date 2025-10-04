from src.app.core.settings import Config
from src.app.core import celery
from datetime import datetime
from src.app.models import User

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



def appointment_success(email: str, user: User, appt_date: datetime):
    """
    Sends a friendly confirmation email after successfully booking an appointment.
    """

    name = user.patient.full_name
    hospital = user.hospital.hospital_name

    # Format appointment date nicely
    date_str = appt_date.strftime("%A, %B %d, %Y at %I:%M %p")

    # HTML body
    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">

            <h2 style="color: #2c3e50; text-align: center;">🎉 Appointment Confirmed!</h2>

            <p style="font-size: 16px; color: #555555; line-height: 1.6;">
                Hi <strong>{name}</strong>,
            </p>

            <p style="font-size: 16px; color: #555555; line-height: 1.6;">
                We’re happy to let you know that your appointment with 
                <strong>{hospital}</strong> has been successfully scheduled for:
            </p>

            <div style="background-color: #f9f9f9; border: 1px solid #eee; padding: 15px; margin: 20px 0; border-radius: 6px; text-align: center;">
                <p style="font-size: 18px; color: #333333; margin: 0;">
                    📅 <strong>{date_str}</strong>
                </p>
            </div>

            <p style="font-size: 16px; color: #555555; line-height: 1.6;">
                Please save this date on your calendar. Don’t panic atol, we’ll also send you a friendly reminder as the day approaches.  
            </p>

            <p style="font-size: 16px; color: #555555; line-height: 1.6;">
                Welcome to the family, {name}! 💙
            </p>
        </div>

        <div style="max-width: 600px; margin: auto; padding: 20px; text-align: center;">
            <p style="font-size: 14px; color: #888888; line-height: 1.6;">
                Please do not reply to this email.  
                If you have any questions, kindly contact us directly through your patient portal.  
            </p>
        </div>
    </body>
    </html>
    """

    subject = "✅ Your Appointment is Confirmed!"

    email_list = [email]

    # Push email to Celery
    celery.send_email_task.delay(email_list, subject, body_html)


def appointment_notification_hospital(email: str, patient: User, appt_date: datetime):
    """
    Sends an email notification to the hospital when a patient books an appointment.
    """
    patient_name = patient.patient.full_name

    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f9fafb; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">

            <h2 style="color: #16a34a;">📅 New Appointment Booked</h2>

            <p style="font-size: 16px; color: #374151;">
                Dear Hospital Admin,
            </p>

            <p style="font-size: 16px; color: #374151;">
                <strong>{patient_name}</strong> has booked an appointment scheduled for 
                <strong>{appt_date.strftime('%A, %B %d, %Y at %I:%M %p')}</strong>.
            </p>

            <p style="font-size: 16px; color: #374151;">
                Please log in to your dashboard to confirm and prepare for this appointment.
            </p>
        </div>

        <div style="max-width: 600px; margin: auto; padding: 30px; text-align: center;">
            <p style="font-size: 14px; color: #6b7280;">
                This is an automated notification from the appointment system.
            </p>
        </div>
    </body>
    </html>
    """

    subject = "📌 New Appointment Notification"

    celery.send_email_task.delay([email], subject, body_html)


#canceled appointment
def appointment_canceled(email: str, user: User, appt_date: datetime):
    """
    Sends an email after an appointment is canceled.
    """

    name = user.patient.full_name
    hospital = user.hospital.hospital_name
    date_str = appt_date.strftime("%A, %B %d, %Y at %I:%M %p")

    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">

            <h2 style="color: #c0392b; text-align: center;">❌ Appointment Canceled</h2>

            <p style="font-size: 16px; color: #555555; line-height: 1.6;">
                Hi <strong>{name}</strong>,
            </p>

            <p style="font-size: 16px; color: #555555; line-height: 1.6;">
                Your appointment with <strong>{hospital}</strong> scheduled for:
            </p>

            <div style="background-color: #f9f9f9; border: 1px solid #eee; padding: 15px; margin: 20px 0; border-radius: 6px; text-align: center;">
                <p style="font-size: 18px; color: #333333; margin: 0;">
                    📅 <strong>{date_str}</strong>
                </p>
            </div>

            <p style="font-size: 16px; color: #555555; line-height: 1.6;">
                has been <strong>canceled</strong>. If this was unintentional or you’d like to rebook, please log in to your patient portal or contact us directly.  
            </p>

            <p style="font-size: 16px; color: #555555; line-height: 1.6;">
                We’re here to assist you anytime 💙.
            </p>
        </div>

        <div style="max-width: 600px; margin: auto; padding: 20px; text-align: center;">
            <p style="font-size: 14px; color: #888888; line-height: 1.6;">
                Please do not reply to this email.  
                If you need help, kindly reach us via your patient portal.  
            </p>
        </div>
    </body>
    </html>
    """

    subject = "❌ Your Appointment Has Been Canceled"
    email_list = [email]
    celery.send_email_task.delay(email_list, subject, body_html)


#rescheduled appointment
def appointment_rescheduled(email: str, name: str, hospital_name: str, old_date: datetime, new_date: datetime):
    """
    Sends an email after an appointment is rescheduled.
    """

    old_str = old_date.strftime("%A, %B %d, %Y at %I:%M %p")
    new_str = new_date.strftime("%A, %B %d, %Y at %I:%M %p")

    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">

            <h2 style="color: #2980b9; text-align: center;">📅 Appointment Rescheduled</h2>

            <p style="font-size: 16px; color: #555555; line-height: 1.6;">
                Hi <strong>{name}</strong>,
            </p>

            <p style="font-size: 16px; color: #555555; line-height: 1.6;">
                We regrest to inform you, due to unforseen circumstances that your appointment with <strong>{hospital_name}</strong> originally scheduled for:
            </p>

            <div style="background-color: #f9f9f9; border: 1px solid #eee; padding: 15px; margin: 15px 0; border-radius: 6px; text-align: center;">
                <p style="font-size: 16px; color: #333333; margin: 0;">
                    ❌ <strong>{old_str}</strong>
                </p>
            </div>

            <p style="font-size: 16px; color: #555555; line-height: 1.6;">
                has been <strong>rescheduled</strong> to:
            </p>

            <div style="background-color: #f0f9ff; border: 1px solid #cce5ff; padding: 15px; margin: 20px 0; border-radius: 6px; text-align: center;">
                <p style="font-size: 18px; color: #2980b9; margin: 0;">
                    ✅ <strong>{new_str}</strong>
                </p>
            </div>

            <p style="font-size: 16px; color: #555555; line-height: 1.6;">
                Please mark this new date on your calendar. We’ll also send you a reminder before your appointment.  
            </p>

            <p style="font-size: 16px; color: #555555; line-height: 1.6;">
                Thank you for your understanding, {name} 💙.
            </p>
        </div>

        <div style="max-width: 600px; margin: auto; padding: 20px; text-align: center;">
            <p style="font-size: 14px; color: #888888; line-height: 1.6;">
                Please do not reply to this email.  
                For assistance, log in to your patient portal.  
            </p>
        </div>
    </body>
    </html>
    """

    subject = "📅 Your Appointment Has Been Rescheduled"
    email_list = [email]
    celery.send_email_task.delay(email_list, subject, body_html)



def hospital_admin_invite(email: str, hospital_name: str, signup_link: str):
    """
    Sends an email invitation to a hospital admin with a secure signup link.
    """

    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f9fafb; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff;
                    border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">

            <h2 style="color: #2563eb; text-align: center;">🎉 You’ve Been Invited!</h2>

            <p style="font-size: 16px; color: #374151;">
                Dear Admin,
            </p>

            <p style="font-size: 16px; color: #374151;">
                <strong>{hospital_name}</strong> has added your email address as a hospital administrator 
                on our healthcare platform. To complete your registration and activate your admin account, 
                please click the secure link below:
            </p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{signup_link}" 
                   style="background-color: #2563eb; color: #ffffff; text-decoration: none;
                          padding: 12px 24px; border-radius: 6px; font-size: 16px;">
                   Complete Your Registration
                </a>
            </div>

            <p style="font-size: 16px; color: #374151;">
                This link is unique to you and will expire in <strong>24 hours</strong> for security reasons.  
                If the button doesn’t work, you can copy and paste this link into your browser:
            </p>

            <p style="font-size: 14px; color: #1d4ed8; word-break: break-all;">
                {signup_link}
            </p>

            <p style="font-size: 16px; color: #374151;">
                If you did not expect this invitation, please ignore this email.
            </p>
        </div>

        <div style="max-width: 600px; margin: auto; padding: 20px; text-align: center;">
            <p style="font-size: 14px; color: #6b7280;">
                This is an automated message from the Appointment System.  
                Please do not reply to this email.
            </p>
        </div>
    </body>
    </html>
    """

    subject = f"Hospital Admin Invitation – {hospital_name}"

    celery.send_email_task.delay([email], subject, body_html)
