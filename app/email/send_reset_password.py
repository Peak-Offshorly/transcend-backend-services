from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.email.send_email import send_email_async
from fastapi import BackgroundTasks
from app.const import(
    EMAIL_FROM,
    EMAIL_FROM_NAME,
    EMAIL_PASSWORD,
    EMAIL_PORT,
    EMAIL_SERVER,
    EMAIL_USERNAME
)

conf = ConnectionConfig(
    MAIL_USERNAME=EMAIL_USERNAME,
    MAIL_PASSWORD=EMAIL_PASSWORD,
    MAIL_FROM=EMAIL_FROM,
    MAIL_PORT=EMAIL_PORT,
    MAIL_SERVER=EMAIL_SERVER,
    MAIL_FROM_NAME="Peak-Transcend",
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    MAIL_STARTTLS=True,
    TEMPLATE_FOLDER="././app/email/templates"
)

async def send_reset_password(email_to: str, link: str):

    subject = "Begin your leadership development journey" 
    body = {"reset_link": link}


    await send_email_async(
        subject=subject,
        email_to=email_to,
        body=body,
        template_name="password-reset-email.html", 
        reply_to=EMAIL_FROM,  
        purpose="reset_password"
    )
    print(f"Sent reset password email to {email_to}")

