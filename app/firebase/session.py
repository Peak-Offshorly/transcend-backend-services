import os
import pyrebase
import firebase_admin
from firebase_admin import credentials, auth

if not firebase_admin._apps:
    cred = credentials.Certificate("././transcend-service-account-key.json")
    firebase_admin.initialize_app(cred)
    print("Firebase Initialized")

firebaseConfig = {
  'apiKey': os.getenv("FIREBASE_CONFIG_APIKEY"),
  'authDomain': os.getenv("FIREBASE_CONFIG_AUTHDOMAIN"),
  'projectId': os.getenv("FIREBASE_CONFIG_PROJECTID"),
  'storageBucket': os.getenv("FIREBASE_CONFIG_STORAGEBUCKET"),
  'messagingSenderId': os.getenv("FIREBASE_CONFIG_MESSAGINGSENDERID"),
  'appId': os.getenv("FIREBASE_CONFIG_APPID"),
  'measurementId': os.getenv("FIREBASE_CONFIG_MEASUREMENTID"),
  'databaseURL': ""
}

firebase=pyrebase.initialize_app(firebaseConfig)
