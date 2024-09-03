from datetime import datetime
import datetime as dt
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.firebase.session import firebase, auth
import firebase_admin
from firebase_admin import auth, credentials
from app.database.models import Users
from app.schemas.models import SignUpSchema, UpdateUserSchema, LoginSchema, UserCompanyDetailsSchema,CustomTokenRequestSchema
from app.database.connection import get_db
from app.firebase.utils import verify_token
from app.utils.users_crud import (
    create_user,
    update_user,
    delete_user,
    get_one_user,
    get_one_user_id,
    get_all_users,
    update_user_company_details,
    get_user_company_details,
    get_all_user_dashboard
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

@router.get("/get-user-uid")
async def get_user_account_uid(user_id: str, db: db_dependency):
  try:
    return get_one_user_id(db=db, user_id=user_id)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
@router.post("/create-user")
async def create_user_account(data: SignUpSchema, db: db_dependency):
    try:
        # create user 
        firebase_user = auth.create_user(
            email=data.email,
            password=data.password,
            display_name=f"{data.first_name} {data.last_name}"
        )

        # send email verification
        verification_link = auth.generate_email_verification_link(data.email)

        # create user in database
        new_account = Users(
            id=firebase_user.uid,
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            mobile_number=data.mobile_number
        )

        create_user(db=db, user=new_account)

        # set user role in Firebase custom claims
        role = 'unknown'  # default role is unknown
        auth.set_custom_user_claims(firebase_user.uid, {'role': role})
        print(f"Create: User role set to {role}")

        return JSONResponse(
            content={
                "message": f"Account successfully created for {data.email}",
                "user_id": firebase_user.uid,
                "email": data.email,
                "display_name": f"{data.first_name} {data.last_name}",
                "verification_link": verification_link
            },
            status_code=200
        )

    except Exception as error:
        # If any error occurs, delete the Firebase user if it was created
        if 'firebase_user' in locals():
            auth.delete_user(firebase_user.uid)
        raise HTTPException(status_code=400, detail=str(error))

@router.post("/login")
async def login_user_account(data: LoginSchema, db: db_dependency):
  token = data.token
  
  try:
    decoded_token = auth.verify_id_token(token)
    email = decoded_token.get('email')
    role = decoded_token.get('role', 'unknown') # default role is unknown
    # print(f"Login: User role set to {role}")
    user_db = get_one_user(db=db, email=email)
    
    session_cookie = firebase_admin.auth.create_session_cookie(token, expires_in=dt.timedelta(minutes=5))

    response = JSONResponse(
      content={
        "message": f"Successfully logged in {email}",
        "token": token,
        "user_id": user_db.id,
        "role": role
        },
      status_code=200
    )
    if role == "admin":
      # check environment to set domain and samesite on dev staging and prod
      # domain = "" BE domain for prod
      # samesite = "lax" # for prod
      # secure= True # for prod
      domain = "transcend-backend-services-4toc.onrender.com"
      samesite = "None" 
      secure=False
    else: None

    if domain:
      response.set_cookie(
        key="__session",
        value=session_cookie,
        httponly=True,
        secure=secure,
        max_age=300,  
        samesite=samesite,
        domain=domain
    )

    # print(f"Login: User role set to {role}")
    return response
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
@router.post("/edit-user")
async def edit_user_account(data: UpdateUserSchema, db: db_dependency, token = Depends(verify_token)):
  user_id = data.id

  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )
  
  email = data.email
  first_name = data.first_name
  last_name = data.last_name
  try:
    update_user(db=db, user_id=user_id, email=email, first_name=first_name, last_name=last_name)

    return JSONResponse(
      content={"message":  f"Account successfully updated for {user_id}"},
      status_code=200
    )
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  

@router.delete("/delete-user")
async def delete_user_account(request: Request, db: db_dependency):
    try:
        # Extract the Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header missing")

        # Extract the token from the Bearer token format
        try:
            id_token = auth_header.split(" ")[1]
        except IndexError:
            raise HTTPException(status_code=401, detail="Authorization header format is invalid")

        # Verify the token and extract the uid
        try:
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token.get("uid")
            email = decoded_token.get("email")  # Get email from the decoded token if available
        except auth.InvalidIdTokenError:
            raise HTTPException(status_code=401, detail="Invalid Firebase ID token")
        except auth.ExpiredIdTokenError:
            raise HTTPException(status_code=401, detail="Expired Firebase ID token")

        if not uid:
            raise HTTPException(status_code=401, detail="Token verification failed, UID not found")

        # Retrieve the user from the database using the email
        user = get_one_user(db=db, email=email)  # Assuming the function expects an 'email'
        if not user:
            raise HTTPException(status_code=404, detail="User not found in the database")

        # Delete the user from Firebase Authentication
        auth.delete_user(uid=uid)

        # Delete the user from the PostgreSQL database
        delete_user(db=db, user_id=uid)

        return JSONResponse(
            content={"message": f"Account successfully deleted for {user.email}"},
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
  
@router.post("/set-user-role")
async def set_user_role(request: Request, db: db_dependency):
    try:

        body = await request.json()
        user_id = body.get("user_id")
        role = body.get("role")

        if not user_id or not role:
            raise HTTPException(status_code=400, detail="user_id and role are required fields")
        
        user = auth.get_user(user_id)
        custom_claims = user.custom_claims or {}
        role_from_claims = custom_claims.get('role', 'unknown')  
        print(f"Current role: {role_from_claims}")
        
        # only two roles are allowed
        if role not in ["admin", "user"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        
        # no repeat role assignment
        if role_from_claims == role:
            raise HTTPException(status_code=400, detail=f"User is already a {role}")
        
        if role == "admin":
           if role_from_claims == "user":
              raise HTTPException(status_code=400, detail="This user can't be promoted to admin")
           if role_from_claims == "unknown":
              auth.set_custom_user_claims(user_id, {'role': role})
              print(f"Set: User role set to {role}")
        if role == "user":
            if role_from_claims == "admin":
                auth.set_custom_user_claims(user_id, {'role': role})
                print(f"Set: User role set to {role}")
            if role_from_claims == "unknown":
                auth.set_custom_user_claims(user_id, {'role': role})
                print(f"Set: User role set to {role}")

        return JSONResponse(
            content={"message": f"User role set to {role}"},
            status_code=200
        )
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
  
@router.get("/get-user-role")
async def get_user_role(request: Request):
    try:
        # extract the Authorization header from the request
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            raise HTTPException(status_code=400, detail="Authorization header is required")

        # extract the token from the header
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=400, detail="Invalid authorization header format")
        
        token = auth_header.split(" ")[1]

        # verify 
        print("Get: Verifying token")
        decoded_token = auth.verify_id_token(token)
        role = decoded_token.get('role', 'unknown')  # default role is 'unknown'
        print(f"Get: User role is {role}")

        # return the response with the role attribute
        return JSONResponse(
            content={"message": f"User role is {role}", "role": role},
            status_code=200
        )

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
    
@router.get("/get-all-users")
async def get_all_users_account(db: db_dependency):
    try:
        users = get_all_user_dashboard(db)
        return users
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
    
@router.post("/view-user")
async def view_user_account(request: Request, db: db_dependency):
    try:
        body = await request.json()
        token = body.get("token")
        user_id = body.get("user_id")

        if not token:
            raise HTTPException(status_code=400, detail="id_token is required")

        # Verify the token and get the role and user_id
        decoded_token = auth.verify_id_token(token)
        role = decoded_token.get('role', 'unknown')  # default role is unknown
        token_user_id = decoded_token.get('user_id')

        # Check if the token belongs to the current logged-in user or if the user is an admin
        if token_user_id != user_id and role != 'admin': 
            raise HTTPException(status_code=403, detail="You do not have permission to view this account")

        # If the checks pass, proceed to retrieve the user details
        return get_one_user_id(db=db, user_id=user_id)
        
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
    
@router.post("/generate-custom-token")
async def generate_custom_token(data:CustomTokenRequestSchema , db: db_dependency):
  try:
    user_id = data.user_id
    custom_token = auth.create_custom_token(user_id)
    decoded_token = custom_token.decode('utf-8')
    return JSONResponse(
      content={"message": "Custom token generated", "custom_token": decoded_token},
        status_code=200)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
