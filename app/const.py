import os
from dotenv import load_dotenv
load_dotenv()

# Firebase Config 
FIREBASE_CONFIG_APIKEY=os.getenv("FIREBASE_CONFIG_APIKEY")
FIREBASE_CONFIG_AUTHDOMAIN=os.getenv("FIREBASE_CONFIG_AUTHDOMAIN")
FIREBASE_CONFIG_PROJECTID=os.getenv("FIREBASE_CONFIG_PROJECTID")
FIREBASE_CONFIG_STORAGEBUCKET=os.getenv("FIREBASE_CONFIG_STORAGEBUCKET")
FIREBASE_CONFIG_MESSAGINGSENDERID=os.getenv("FIREBASE_CONFIG_MESSAGINGSENDERID")
FIREBASE_CONFIG_APPID=os.getenv("FIREBASE_CONFIG_APPID")
FIREBASE_CONFIG_MEASUREMENTID= os.getenv("FIREBASE_CONFIG_MEASUREMENTID")

#Postresql Connection Config
SQLALCHEMY_DATABASE_URL=os.getenv('SQLALCHEMY_DATABASE_URL')

#Email Credentials
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_PORT = int(os.getenv('EMAIL_PORT'))
EMAIL_SERVER = os.getenv('EMAIL_SERVER')
EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME')

#Web App URLs
WEB_URL = os.getenv('WEB_URL')

# Gmail API Constants
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
# TOKEN_FILE = 'token.json'
TOKEN_FILE = os.environ.get('TOKEN_FILE', '/etc/secrets/token')
# CREDENTIALS_FILE = 'credentials.json'
CREDENTIALS_FILE = os.environ.get('CREDENTIALS_FILE', '/etc/secrets/credentials')
TEMPLATE_FOLDER = "././app/email/templates"
REDIRECT_URI = 'http://localhost:5173/oauth2callback'

# Fireflies API Key
FIREFLIES_API_KEY = os.getenv('FIREFLIES_API_KEY')