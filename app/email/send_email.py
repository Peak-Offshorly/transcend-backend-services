from typing import Dict, Any
from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
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
    MAIL_FROM_NAME=EMAIL_FROM_NAME,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    MAIL_STARTTLS=True,
    TEMPLATE_FOLDER="././app/email/templates"
)

def send_email_background(background_tasks: BackgroundTasks, subject: str, email_to: str, body: Dict[str, Any], template_name: str, reply_to: str):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        template_body=body,
        subtype=MessageType.html,
        reply_to=[reply_to]
    )

    fm = FastMail(conf)
    background_tasks.add_task(
        fm.send_message,
        message,
        template_name=template_name
    )

async def send_email_async(subject: str, email_to: str, body: Dict[str, Any], template_name: str, reply_to: str, purpose: str):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        template_body=body,
        subtype=MessageType.html,
        reply_to=[reply_to]
    )
    if purpose == "reset_password" or purpose == "complete_profile":
        conf.MAIL_FROM_NAME = "Transcend Team"
    fm = FastMail(conf)
    await fm.send_message(message, template_name=template_name)