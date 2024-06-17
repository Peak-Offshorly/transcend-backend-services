from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.firebase.session import firebase, auth
from app.database.models import Users
from app.schemas.models import SignUpSchema, UpdateUserSchema, LoginSchema, UserCompanyDetailsSchema
from app.database.connection import get_db
from app.firebase.utils import verify_token
from app.utils.users_crud import (
    create_user,
    update_user,
    delete_user,
    get_one_user,
    get_all_users,
    update_user_company_details,
    get_user_company_details
)
db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.post("/save-company-details")
async def save_company_details(data: UserCompanyDetailsSchema, db: db_dependency, token = Depends(verify_token)):
  user_id = data.id

  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )

  company_size = data.company_size
  industry = data.industry
  role = data.role
  role_description = data.role_description
  try:
    update_user_company_details(
      db=db,
      user_id=user_id,
      company_size=company_size,
      industry=industry,
      role=role,
      role_description=role_description
    )

    return JSONResponse(
      content={"message":  "Company details saved."},
      status_code=200
    )
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

@router.get("/get-company-details")
async def get_company_details(user_id: str, db: db_dependency, token = Depends(verify_token)):
  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )
  
  try:
    return get_user_company_details(db=db, user_id=user_id)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

@router.get("/get-user")
async def get_user_account(email: str, db: db_dependency):
  try:
    return get_one_user(db=db, email=email)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
@router.post("/create-user")
async def create_user_account(data: SignUpSchema, db: db_dependency):
  uid = data.uid
  email = data.email
  first_name = data.first_name
  last_name = data.last_name

  try:
    new_account = Users(
      id = uid,
      email = email,
      first_name = first_name,
      last_name = last_name
    )

    create_user(db=db, user=new_account)
    
    return JSONResponse(
      content={
        "message":  f"Account successfully created for {email}",
        "user_id": new_account.id
        },
      status_code=200
    )
  
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
@router.post("/login")
async def login_user_account(data: LoginSchema, db: db_dependency):
  email = data.email
  password = data.password

  try:
    user = firebase.auth().sign_in_with_email_and_password(
      email = email,
      password = password
    )

    token = user["idToken"]
    user_db = get_one_user(db=db, email=email)
    
    return JSONResponse(
      content={
        "message": f"Successfully logged in {email}",
        "token": token,
        "user_id": user_db.id
        },
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
    user = get_one_user(db=db, email=email)
    #---

    auth.update_user(
      uid=user.id,
      email = data.email
    )

    update_user(db=db, user_id=user.id, first_name=first_name, last_name=last_name)

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
    user = get_one_user(db=db, email=email)
    #---

    auth.delete_user(
      uid=user.id
    )

    delete_user(db=db, user_id=user.id)

    return JSONResponse(
      content={"message":  f"Account successfully deleted for {user.email}"},
      status_code=200
    )
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
@router.get("/check-if-active")
async def check_if_active_user(db: db_dependency):
  try:
    print("---IS USER ACTIVE CHECKING STARTED---")
    users_db = await get_all_users(db)

    # Set a threshold for considering a user as active - set threshold to 30 days
    activity_threshold_seconds = 30 * 24 * 60 * 60  # 30 days in seconds
    
    for user_db in users_db:
      user = auth.get_user_by_email(user_db.email)
      # Get the last sign-in timestamp from the Firebase user object
      last_sign_in_timestamp = user.user_metadata.last_sign_in_timestamp or 0
      # Get the current time
      current_time = datetime.now().timestamp()
      # Calculate the time difference in seconds since the last sign-in
      time_difference_seconds = current_time - (last_sign_in_timestamp / 1000)  # Convert milliseconds to seconds

      # Check if the user's last sign-in was within the activity threshold
      if time_difference_seconds <= activity_threshold_seconds:
        user_db.is_active = True
        print(f"{user_db.email} is active")
      else:
        user_db.is_active = False
        print(f"{user_db.email} is inactive")
    
    db.commit()
    print("---IS USER ACTIVE CHECKING FINISHED---")
    return JSONResponse(
        content={"message": "IS USER ACTIVE CHECKING FINISHED"},
        status_code=200
    )
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))