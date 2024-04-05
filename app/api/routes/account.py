from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.firebase.session import firebase, auth
from app.database.models import Accounts
from app.schemas.models import SignUpSchema, LoginSchema
from app.database.connection import get_db
from app.utils.accounts_crud import create_account

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.get("/user")
async def get_user_account():
  try:
    return { "message": "User Account" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
@router.post("/create-user")
async def create_user_account(data: SignUpSchema, db: db_dependency):
  email = data.email
  password = data.password
  first_name = data.first_name
  last_name = data.last_name

  try:
    user = auth.create_user(
      email = email,
      password = password
    )
    
    #TODO: hash password; or password might not be needed in PostrgreSQL DB 
    new_account = Accounts(
      id = user.uid,
      email = email,
      password = password,
      first_name = first_name,
      last_name = last_name
    )

    create_account(db=db, account=new_account)
    
    return JSONResponse(
      content={"message":  f"User account created successfuly for {user.email}"},
      status_code=200
    )
  
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
@router.post("/login")
async def login_user_account(data: LoginSchema):
  email = data.email
  password = data.password

  try:
    user = firebase.auth().sign_in_with_email_and_password(
      email = email,
      password = password
    )

    token = user["idToken"]
    
    return JSONResponse(
      content={"token": token},
      status_code=200
    )
  
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

