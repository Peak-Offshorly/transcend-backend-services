from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.firebase.session import firebase, auth
from app.database.models import Users
from app.schemas.models import SignUpSchema, UpdateUserSchema, LoginSchema
from app.database.connection import get_db
from app.utils.users_crud import (
    create_user,
    update_user,
    delete_user,
    get_one_user
)
db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/accounts", tags=["accounts"])

global token 

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
    
    new_account = Users(
      id = user.uid,
      email = email,
      first_name = first_name,
      last_name = last_name
    )

    create_user(db=db, user=new_account)
    
    return JSONResponse(
      content={"message":  f"Account successfully created for {user.email}"},
      status_code=200
    )
  
  except auth.EmailAlreadyExistsError:
    raise HTTPException(status_code=400, detail="Email is already used.")
  
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
  
@router.post("/update-user")
async def update_user_account(data: UpdateUserSchema, db: db_dependency):
  email = data.email
  first_name = data.first_name
  last_name = data.last_name

  try:
    ### ACTUAL IMPLEMENTATION: Should get tokenId from logged-in user then use that to verify and obtain the uid of the user.
   
    #---TEST IMPLEMENTATION
    user = get_one_user(db=db, account_email=email)
    #---

    auth.update_user(
      uid=user.id,
      email = data.email
    )

    update_user(db=db, account_id=user.id, first_name=first_name, last_name=last_name)

    return JSONResponse(
      content={"message":  f"Account successfully updated for {user.email}"},
      status_code=200
    )
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  

@router.delete("/delete-user")
async def delete_user_account(email: str, db: db_dependency):
  try:
    
    ### ACTUAL IMPLEMENTATION: Should get tokenId from logged-in user then use that to verify and obtain the uid of the user.
    #---TEST IMPLEMENTATION
    user = get_one_user(db=db, account_email=email)
    #---

    auth.delete_user(
      uid=user.id
    )

    delete_user(db=db, account_id=user.id)

    return JSONResponse(
      content={"message":  f"Account successfully deleted for {user.email}"},
      status_code=200
    )
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))