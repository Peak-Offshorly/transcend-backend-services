from typing import Dict, Any
from fastapi import BackgroundTasks
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from email.mime.text import MIMEText
import base64
from googleapiclient.discovery import build
import os
from jinja2 import Environment, FileSystemLoader
from app.const import(
    EMAIL_FROM,
    EMAIL_FROM_NAME,
    EMAIL_PASSWORD,
    EMAIL_PORT,
    EMAIL_SERVER,
    EMAIL_USERNAME,
    SCOPES,
    TOKEN_FILE,
    CREDENTIALS_FILE,
    TEMPLATE_FOLDER,
    REDIRECT_URI
)

# Handles OAuth 2.0 flow and returns a Gmail service object.
def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            return None  # Trigger the OAuth flow
    return build('gmail', 'v1', credentials=creds)

# Creates an email message in the format required by Gmail API.
def create_message(sender: str, to: str, subject: str, message_text: str, reply_to: str = None, purpose: str = None):
    message = MIMEText(message_text, 'html')
    message['to'] = to

    if purpose in ["reset_password", "complete_profile", "verify_account"]:
        sender_name = "Transcend Team"
    else:
        sender_name = "Transcend AI" #CHANGE THIS TO ENV VALUE ONCE WORKING
    
    # Format the 'from' field with the appropriate name and email
    message['from'] = f"{sender_name} <{sender}>"
    message['subject'] = subject
    if reply_to:
        message['reply-to'] = reply_to
    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

# Sends the email using the Gmail API.
def send_message(service, user_id: str, message: Dict[str, Any]):
    try:
        message = service.users().messages().send(userId=user_id, body=message).execute()
        print(f"Message Id: {message['id']}")
        return message
    except Exception as e:
        print(f"An error occurred: {e}")
        raise Exception

# Renders the email template (using Jinja2, which you'll need to install).
def render_template(template_name: str, context: Dict[str, Any]) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATE_FOLDER))
    template = env.get_template(template_name)
    return template.render(context)

def send_email_background(background_tasks: BackgroundTasks, subject: str, email_to: str, body: Dict[str, Any], template_name: str, reply_to: str):
    background_tasks.add_task(
        send_email_async,
        subject,
        email_to,
        body,
        template_name,
        reply_to
    )

async def send_email_async(subject: str, email_to: str, body: Dict[str, Any], template_name: str, reply_to: str, purpose: str = None):
    service = get_gmail_service()
    sender = "coach@peakleadershipinstitute.com" 

    if not service:
        # Redirect to start OAuth flow
        return RedirectResponse(url="/start_oauth")
    
    # Render the email body using the template
    message_text = render_template(template_name, body)
    
    # Create the email message
    email_message = create_message(sender, email_to, subject, message_text, reply_to, purpose)
    
    # Send the email
    try:
        send_message(service, "me", email_message)
    except Exception as e:
        print(f"An error occurred: {e}")
        raise Exception


def setup_oauth_flow():
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE, 
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    print(f"Please go to this URL to authorize the application: {auth_url}")
    
    code = input("Enter the authorization code: ")
    
    flow.fetch_token(code=code)
    creds = flow.credentials
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
    print("OAuth flow completed and credentials saved.")

# Remove comment for manual generation of token file through OAuth2
# setup_oauth_flow()