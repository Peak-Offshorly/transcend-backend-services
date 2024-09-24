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

# Reusing the email configuration (conf) from your current setup
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

async def send_complete_profile(email_to: str, link: str, firstname: str, lastname: str):

    subject = "Begin your leadership development journey" 
    body = {
        "personal_form": link, 
        "admin_firstname": firstname, 
        "admin_lastname": lastname}


    await send_email_async(
        subject=subject,
        email_to=email_to,
        body=body,
        template_name="complete-profile-email.html", 
        reply_to=EMAIL_FROM,  
        purpose="complete_profile"
    )
    print(f"Sent complete profile email to {email_to}")

