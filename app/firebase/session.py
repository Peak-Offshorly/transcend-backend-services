import pyrebase
import firebase_admin
from firebase_admin import credentials, auth
from app.const import (
    FIREBASE_CONFIG_APIKEY,
    FIREBASE_CONFIG_AUTHDOMAIN,
    FIREBASE_CONFIG_PROJECTID,
    FIREBASE_CONFIG_STORAGEBUCKET,
    FIREBASE_CONFIG_MESSAGINGSENDERID,
    FIREBASE_CONFIG_APPID,
    FIREBASE_CONFIG_MEASUREMENTID,
)

if not firebase_admin._apps:
    # Render path for service key
    cred = credentials.Certificate("/etc/secrets/transcend-service-account-key")

    # cred = credentials.Certificate("././transcend-service-account-key.json")
    firebase_admin.initialize_app(cred)
    print("Firebase Initialized")

firebaseConfig = {
  'apiKey': FIREBASE_CONFIG_APIKEY,
  'authDomain': FIREBASE_CONFIG_AUTHDOMAIN,
  'projectId': FIREBASE_CONFIG_PROJECTID,
  'storageBucket': FIREBASE_CONFIG_STORAGEBUCKET,
  'messagingSenderId': FIREBASE_CONFIG_MESSAGINGSENDERID,
  'appId': FIREBASE_CONFIG_APPID,
  'measurementId': FIREBASE_CONFIG_MEASUREMENTID,
  'databaseURL': ""
}

firebase=pyrebase.initialize_app(firebaseConfig)
