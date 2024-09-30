from datetime import datetime, timedelta, timezone
import datetime as dt
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Annotated
from app.firebase.session import firebase, auth
import firebase_admin
from firebase_admin import auth, credentials, storage
from app.database.models import Users, UserInvitation
from app.schemas.models import SignUpSchema, UpdateUserSchema, LoginSchema, UserCompanyDetailsSchema,CustomTokenRequestSchema, AddUserToCompanySchema, AddUserToCompanyDashboardSchema, PasswordChangeRequest, UpdatePersonalDetailsSchema, ResetPasswordRequest, UpdateFirstAndLastNameSchema, ResendLinkSchema
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
    get_all_user_dashboard,
    add_user_to_company_crud,
    create_user_in_dashboard,
    get_latest_sprint_for_user,
    update_personal_details,
    update_user_photo,
    update_first_and_last_name,
    create_user_invitation
)
from app.utils.company_crud import get_company_by_id
from app.email.send_reset_password import send_reset_password
from app.email.send_complete_profile_email import send_complete_profile
from app.email.send_verification_email import send_verification_email
from typing import List
from firebase_admin.exceptions import FirebaseError
import requests
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from uuid import uuid4
import os
import secrets

db_dependency = Annotated[Session, Depends(get_db)]
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/accounts", tags=["accounts"])
firebase_auth = HTTPBearer()
bucket = storage.bucket()

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
            mobile_number=data.mobile_number,
            acc_activated=True,
            user_type = 'unknown'
        )

        create_user(db=db, user=new_account)
        # send verification email
        await send_verification_email(data.email, verification_link)

        return JSONResponse(
            content={
                "message": f"Account successfully created for {data.email}",
                "user_id": firebase_user.uid,
                "email": data.email,
                "display_name": f"{data.first_name} {data.last_name}",
                "verification_link": verification_link,
                "user_type": new_account.user_type
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
  email = data.email
  password = data.password

  try:
    user = firebase.auth().sign_in_with_email_and_password(
      email = email,
      password = password
    )

    token = user["idToken"]
    decoded_token = auth.verify_id_token(token)
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
      response.set_cookie(
              key="__session",
              value=session_cookie,
              httponly=True,
              secure=True,
              max_age=100,  
              samesite="strict",  
              domain="127.0.0.1"  # domain if deployed = ".netlify.app"  for local use "127.0.0.1"
        )
    if role == "member":
      response.set_cookie(
              key="__session",
              value=session_cookie,
              httponly=True,
              secure=True,
              max_age=100,  
              samesite="strict",  
              domain="127.0.0.1"  # domain if deployed = "peak-transcend-dev.netlify.app"
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
  mobile_number = data.mobile_number
  try:
    update_user(db=db, user_id=user_id, email=email, first_name=first_name, last_name=last_name, mobile_number=mobile_number)

    return JSONResponse(
      content={"message":  f"Account successfully updated for {user_id}"},
      status_code=200
    )
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  

@router.delete("/delete-user")  # must be userid
async def delete_user_account(user_id: str, db: db_dependency):
    """
    Deletes a user account from the database and Firebase Authentication.

    Args:
        email (str): The email of the user to be deleted.
        db (Session): The database session for performing the deletion operation.

    Returns:
        dict: A JSON response with a success message.

    Example output:
        JSON response format:
        {
            "message": "Account successfully deleted for will@offshorly.com",
            "success": true
        }

    Query Params:
        email: The email of the user to be deleted.
    """
    try:
        # check if the email parameter is provided
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID query parameter is required")

        # retrieve the user from the database using the email
        user = get_one_user_id(db=db, user_id=user_id)  
        if not user:
            raise HTTPException(status_code=404, detail="User not found in the database")

        # get the user ID (uid) from the database user object
        uid = user.id

        company = get_company_by_id(db=db, company_id=user.company_id)
        if company:
            if user.user_type == 'admin' and company.admin_count > 0:
                company.admin_count -= 1
            if user.user_type == 'member' and company.member_count > 0:
                company.member_count -= 1
            db.commit()
            
        # Delete the user from Firebase Authentication
        auth.delete_user(uid=uid)

        # Delete the user from the PostgreSQL database
        delete_user(db=db, user_id=uid)

        return JSONResponse(
            content={"message": f"Account successfully deleted for {user.email}", "success": True},
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
    """
    Sets the role of a user in the database.

    Args:
        request (Request): The HTTP request object containing the user details.
        db (Session): The database session for updating the user's role.

    Returns:
        dict: A JSON response with a success message.

    Example output:
        JSON response format:
        {
            "message": "User role set to admin",
            "success": true
        }

    Request Body:
        {
            "user_id": "v1OVQn3QELZpxk3nNmudJ9GtQRp2",
            "role": "member"
        }
    """

    try:
        body = await request.json()
        user_id = body.get("user_id")
        role = body.get("role")

        if not user_id or not role:
            raise HTTPException(status_code=400, detail="user_id and role are required fields")
        
        # only two roles are allowed
        if role not in ["admin", "member"]:
            raise HTTPException(status_code=400, detail="Invalid role")

        user = get_one_user_id(db=db, user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found in the database")
        if user.user_type != 'unknown':
            raise HTTPException(status_code=400, detail="User role already set")   
        
        user_user_type = user.user_type
       
        # no repeat role assignment
        if user_user_type == role:
            raise HTTPException(status_code=400, detail=f"User is already a {role}")
        

        user.user_type = role
        db.commit()

        return JSONResponse(
            content={"message": f"User role set to {role}", "success": True},
            status_code=200
        )
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
  
@router.get("/get-user-role")
async def get_user_role(request: Request, db: db_dependency):
    """
    Gets the role of the user from Firebase Authentication custom claims.

    Args:
        request (Request): The HTTP request object containing the necessary headers.

    Returns:
        dict: A JSON response with a success message and the user's role.

    Example Response:
        {
            "message": "User role is admin",
            "role": "admin"
        }

    Headers:
        Authorization: Bearer <ID token>
    """

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
        current_user_id = decoded_token.get("uid")
        user = get_one_user_id(db=db, user_id=current_user_id)
        role = user.user_type
        print(f"Get: User role is {role}")

        # return the response with the role attribute
        return JSONResponse(
            content={"message": f"User role is {role}", "role": role},
            status_code=200
        )

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))

@router.get("/get-user-role-db")
async def get_user_type_db(user_id: str, db: db_dependency):
    """
    Gets the role of the user from the database.

    Args:
        user_id (str): The user ID to query the role from the database.
        db (Session): The database session for querying the user's role.

    Returns:
        dict: A JSON response with a success message and the user's role.

    Example Response:
        {
            "message": "User role is admin",
            "role": "admin"
        }

    Query Params:
        user_id: The user ID to query the role from the database.
    """

    try:
        user = get_one_user_id(db=db, user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_type = user.user_type
        return JSONResponse(
            content={"message": f"User role is {user_type}", "role": user_type},
            status_code=200
        )

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
    
@router.get("/get-all-users")
async def get_all_users_account(request: Request, db: db_dependency):
    """
    Retrieves the list of all users for the admin dashboard.

    Args:
        request (Request): The HTTP request object containing the necessary headers.
        db (Session): The database session used to query the users.

    Returns:
        list: A list of all users in the database.

    Request Body:
        {
            "user_email": "will@offshorly.com"
        }
    """

    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header is missing")

        id_token = auth_header.split(" ")[1]
        decoded_token = auth.verify_id_token(id_token)
        current_user_id = decoded_token.get("uid")
        
        user = get_one_user_id(db=db, user_id=current_user_id)

        company = user.company_id
        users = get_all_user_dashboard(db,company)
        return users
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
    

@router.post("/view-user")
async def view_user_account(request: Request, db: db_dependency):
    try:
        body = await request.json()
        user_id = body.get("user_id")

        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header is missing")

        id_token = auth_header.split(" ")[1]
        decoded_token = auth.verify_id_token(id_token)
        current_user_id = decoded_token.get("uid")

        current_user = db.query(Users).filter(Users.id == current_user_id).first()

        if not current_user:
            raise HTTPException(status_code=404, detail="Current user not found")
        # print(f"Current user: {current_user.email}\n Current user role: {current_user.role}")
        # check if the current user is an admin or if they're viewing their own profile
        if current_user.user_type == 'admin' or current_user.id == user_id:
            requested_user = get_one_user_id(db=db, user_id=user_id)
            if not requested_user:
                raise HTTPException(status_code=404, detail="Requested user not found")
            
            # get the latest sprint number for the requested user
            latest_sprint_number = get_latest_sprint_for_user(db, user_id)

            first_name = requested_user.first_name if requested_user.first_name is not None else None
            last_name = requested_user.last_name if requested_user.last_name is not None else None

            return {
                "first_name": first_name,
                "last_name": last_name,
                "email": requested_user.email,
                "role": requested_user.role,
                "latest_sprint_number": latest_sprint_number,  # Include latest sprint number
                "user_type": requested_user.user_type,
                "user_photo_url": requested_user.user_photo_url
            }
        else:
            raise HTTPException(status_code=403, detail="You do not have permission to view this account")

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
    
@router.post("/generate-custom-token")
async def generate_custom_token(data:CustomTokenRequestSchema , db: db_dependency):
    """
    Generates a custom token for a user using Firebase Authentication.

    Args:
        data (CustomTokenRequestSchema): The request data containing the user ID.
        db (db_dependency): The database dependency for performing operations (if required).

    Returns:
        dict: A JSON response with a success message and the generated custom token.

    Example Response:
        {
            "message": "Custom token generated",
            "custom_token": "<generated_custom_token>"
        }
    
    Request Body:
    {
        "user_id":"kWxHZ2au8oYyxXibTBIcvYCA1b93"
    }
    """


    try:
        user_id = data.user_id
        custom_token = auth.create_custom_token(user_id)
        decoded_token = custom_token.decode('utf-8')
        return JSONResponse(
            content={"message": "Custom token generated", "custom_token": decoded_token},
            status_code=200)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))

@router.get("/verify-admin")
async def verify_admin(request: Request):
    try:
      session_cookie = request.cookies.get('__session')
      if not session_cookie:
        raise HTTPException(status_code=401, detail="Session cookie not found")
      decoded_claims = auth.verify_session_cookie(session_cookie, check_revoked=True)
      user_id = decoded_claims.get('uid')
      user_role = decoded_claims.get('role', 'unknown')
      return JSONResponse(
            content={"message": "Session verified successfully", "user_id": user_id, "role": user_role},
            status_code=200
        )
    
    except auth.InvalidSessionCookieError:
        raise HTTPException(status_code=401, detail="Invalid session cookie")
    except auth.ExpiredSessionCookieError:
        raise HTTPException(status_code=401, detail="Session cookie has expired")
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))

  
@router.post("/add-user-to-company")
async def add_user_to_company(
   request: Request, 
   data: AddUserToCompanySchema, 
   db: db_dependency
   ):
    """
    Add a user to a company in the database.

    Args:
        data (AddUserToCompanySchema): The request data containing the user ID and company ID.
        db (Session): The database session for performing the operation.
    
    Returns:
        dict: A JSON response with a success message.
    
    Example Response:
        {
            "message": "User with ID PZsrWyyv4yQQmW1OEipC3aZF33q1 has been successfully added to the company with ID be7d9689-3117-5819-9ffe-fa2b9ca205fb.",
            "user_id": "PZsrWyyv4yQQmW1OEipC3aZF33q1",
            "company_id": "be7d9689-3117-5819-9ffe-fa2b9ca205fb",
            "success": true
        }

    Request Body:
        {
            "user_id":"PZsrWyyv4yQQmW1OEipC3aZF33q1",
            "company_id":"be7d9689-3117-5819-9ffe-fa2b9ca205fb"
        }
    """
    try:
        
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header is missing")

        # verify the token 
        id_token = auth_header.split(" ")[1]
        decoded_token = auth.verify_id_token(id_token)
        current_user_id = decoded_token.get("uid")

        if not current_user_id:
            raise HTTPException(status_code=401, detail="Invalid token or user ID not found")

        # fetch the current user from the database
        current_user = db.query(Users).filter(Users.id == current_user_id).first()
        if not current_user:
            raise HTTPException(status_code=404, detail="Current user not found")

        # ensure the current user is an admin
        if current_user.user_type != "admin":
            raise HTTPException(status_code=403, detail="Only admins can access this endpoint")

        # use the current user's company ID
        current_user_company_id = current_user.company_id
        if not current_user_company_id:
            raise HTTPException(status_code=400, detail="Current user's company ID not found")

        user = get_one_user_id(db=db, user_id=data.user_id)
 
        user_company = get_company_by_id(db=db, company_id=user.company_id)
        current_user_company = get_company_by_id(db=db, company_id=current_user_company_id)
        if user_company:
            raise HTTPException(status_code=400, detail="User already belongs to a company")

        # proceed with adding the user to the current user's company
        user_id = data.user_id
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is a required field")

        updated_user = add_user_to_company_crud(db=db, user_id=user_id, company_id=current_user_company_id)

        current_user_company.member_count += 1
        db.commit()

        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found or could not be added to the company")

        return {
            "message": f"User with ID {user_id} has been successfully added to the company with ID {current_user_company_id}.",
            "user_id": updated_user.id,
            "company_id": updated_user.company_id,
            "success": True
        }

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))

@router.post("/add-user-to-company-dashboard")
async def add_user_to_company_dashboard(
   request: Request,
   data: List[AddUserToCompanyDashboardSchema], 
   db: db_dependency
   ):
    """
    Adds multiple users to the company dashboard and creates an account in both Firebase and the database.

    Args:
        data (list[AddUserToCompanyDashboardSchema]): The request data containing multiple user entries.
        db (Session): The database session for performing the operation.

    Returns:
        dict: A JSON response with success messages, user IDs, and emails for all users.

    Example Response:
    {
        "success": true,
        "users": [
            {
                "message": "Account successfully created for flureta@up.edu.ph",
                "user_id": "eRnrtiGbSbOXVl14RPfnFcz5x7j2",
                "email": "flureta@up.edu.ph"
            },
            {
                "message": "Account successfully created for will@offshorly.com",
                "user_id": "Yd9Wt2H94iWnncZrkIAJAniDH853",
                "email": "will@offshorly.com"
            }
        ]
    }

    Request Body:
        [
            {
                "user_email": "flureta@up.edu.ph",
                "user_role": "user"
            },
            {
                "user_email": "will@offshorly.com",
                "user_role": "user"
            }
        ]

    """

    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header is missing")
        id_token = auth_header.split(" ")[1]
        decoded_token = auth.verify_id_token(id_token)
        current_user_id = decoded_token.get("uid")

        # check if the user's email is verified
        if not decoded_token.get("email_verified"):
            raise HTTPException(status_code=403, detail="Email address not verified. Please verify your email before proceeding.")

        current_user = get_one_user_id(db=db, user_id=current_user_id)

        if not current_user:
            raise HTTPException(status_code=404, detail="Current user not found")
    
        current_user_company_id = current_user.company_id
        current_user_first_name = current_user.first_name
        current_user_last_name = current_user.last_name

        
        if current_user.user_type != "admin":
            raise HTTPException(status_code=403, detail="Only admins can access this endpoint")

        if not current_user_company_id:
            raise HTTPException(status_code=400, detail="Current user's company ID not found")
        
        current_user_company = get_company_by_id(db=db, company_id=current_user_company_id)

        response_data = []

        for entry in data:
            user_email = entry.user_email
            user_role = entry.user_role

            if not user_email or not user_role:
                raise HTTPException(status_code=400, detail="user_email and user_role are required fields")
            
            if user_role not in ["admin", "member"]:
                raise HTTPException(status_code=400, detail="Invalid role")
            
            # create a new user in Firebase
            try:
                firebase_user = auth.create_user(
                    email=user_email,
                    email_verified=False,
                    disabled=False
                )

            except Exception as firebase_error:
                raise HTTPException(status_code=400, detail=f"Error creating user in Firebase: {str(firebase_error)}")

            # create the user in the database
            new_user = Users(
                id=firebase_user.uid,
                email=user_email,
                acc_activated=False,
                company_id=current_user_company_id,
                user_type=user_role,
            )

            created_user = create_user_in_dashboard(db=db, user=new_user)
            if user_role == "admin":
                current_user_company.admin_count += 1
            if user_role == "member":
                current_user_company.member_count += 1
            db.commit()

            # create the oob_code and the expiration_time for the new_invitation
            oob_code = secrets.token_urlsafe(32)
            expiration_time = datetime.now(timezone.utc) + timedelta(hours=24)  # OOB code expires in 24 hours
            
            created_invitation = create_user_invitation(db=db, user=new_user, oob_code=oob_code, expiration_time=expiration_time)

            # Send complete profile email
            link = f"https://app.peakleadershipinstitute.com/update-invite-user?oob={oob_code}"
            await send_complete_profile(firebase_user.email, link, current_user_first_name, current_user_last_name)

            # Add success response for the current user
            response_data.append({
                "message": f"Account successfully created for {new_user.email}",
                "user_id": firebase_user.uid,
                "email": entry.user_email,
                "oob_code": oob_code
            })

        # Return the response data for all users
        return JSONResponse(
            content={
                "success": True,
                "users": response_data
            },
            status_code=200
        )

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    credentials: HTTPAuthorizationCredentials = Depends(firebase_auth)
):
    """
    Changes the password of the user

    Args:
        request (PasswordChangeRequest): The request data containing the old and new passwords.
        credentials (HTTPAuthorizationCredentials): The HTTP Authorization credentials containing the Firebase ID token.

    Returns:
        dict: A JSON response with a success message.
    
    Example Response:
        {
            "message": "Password updated successfully", 
            "success": True
        }
    
    Request Body:
        {
            "new_password": "new_password",
            "old_password": "old_password"
        }
    """
    try:
        token = credentials.credentials

       
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']

     
        user = auth.get_user(uid)
        email = user.email

        # verify the old password by attempting to log in
        try:
            firebase_user = firebase.auth().sign_in_with_email_and_password(
                email=email,
                password=request.old_password
            )

            # if login is successful, continue with the password update
        except Exception as login_error:
            raise HTTPException(
                status_code=400,
                detail="Old password is incorrect"
            )

        # Update the user's password in Firebase
        auth.update_user(
            uid,
            password=request.new_password
        )

        return {"message": "Password updated successfully", "success": True}

    except FirebaseError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error updating password: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/complete-profile-details")
async def edit_personal_details(oob_code: str, data: UpdatePersonalDetailsSchema, db: db_dependency, request: Request):
  """
    Changes the personal details and password of the user

    Args:
        request: The request object containing the user token.

    Returns:
        dict: A JSON response with a success message.
    
    Example Response:
        {
            "message": "Account successfully updated for {userID}"
        }
    
    Request Body:
        {
            "first_name": "first_name",
            "last_name": "last_name",
            "mobile_number": "mobile_number",
            "job_title": "job_title",
            "password": "password"
        }
  """
  try:
    # Verify the OOB code and get the invitation
    invitation = db.query(UserInvitation).filter(
        UserInvitation.oob_code == oob_code,
        UserInvitation.expiration_time > datetime.now(timezone.utc)
    ).first()

    if not invitation:
        raise HTTPException(status_code=400, detail="Invalid or expired invitation code")
    
    current_user_id = invitation.user_id

    # retrieve the user from the database using the user_id parameter
    user = get_one_user_id(db=db, user_id=current_user_id)  
    if not user:
        raise HTTPException(status_code=404, detail="User not found in the database")

    # get the current user from the database
    current_user = db.query(Users).filter(Users.id == current_user_id).first()
    if not current_user:
        raise HTTPException(status_code=400, detail="Current user not found")

    first_name = data.first_name
    last_name = data.last_name
    mobile_number = data.mobile_number
    job_title = data.job_title
    update_personal_details(db=db, user_id=current_user_id, first_name=first_name, last_name=last_name, mobile_number=mobile_number, job_title=job_title)
    
    # Update the user's password in Firebase
    auth.update_user(
        current_user_id,
        password=data.password
    )

    # Delete the used invitation
    db.delete(invitation)
    db.commit()

    return JSONResponse(
      content={"message":  f"Account successfully updated for {current_user_id}"},
      status_code=200
    )
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))


@router.post("/request-password-reset")
@limiter.limit("1/minute")  # Apply rate limiting
async def request_password_reset(request: Request, data: ResetPasswordRequest, db: db_dependency):
    """
    Endpoint to request a password reset link for a user's email.

    Returns:
        dict: A JSON response with a success message.
    
    Example Response:
        {
            "success": True,
            "message": "Password reset link sent to user_email"
        }
    
    Request Body:
        {
            "email": "user_email"
        }
    """
    user_email = data.email
    if not user_email:
        raise HTTPException(status_code=400, detail="Email is required")

    try:
        user = auth.get_user_by_email(user_email)
        link = auth.generate_password_reset_link(user_email)
        await send_reset_password(user_email, link)
        return {"success": True, "message": f"Password reset link sent to {user_email}"}
    except auth.UserNotFoundError:
        raise HTTPException(status_code=404, detail="User with this email does not exist")
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
    
@router.post("/update-user-type")
async def update_user_type(request: Request, db: db_dependency):
    """
    Updates the user type of a user in the database.

    Args:
        data (dict): The request data containing the user ID and user type.
        db (Session): The database session for performing the operation.

    Returns:
        dict: A JSON response with a success message.

    Example Response:
        {
            "message": "User type updated successfully",
            "success": True
        }
    

    """
    try:

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header is missing")

        id_token = auth_header.split(" ")[1]
        decoded_token = auth.verify_id_token(id_token)
        current_user_id = decoded_token.get("uid")

        current_user = get_one_user_id(db=db, user_id=current_user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="Current user not found")

        if current_user.user_type != "admin":
            raise HTTPException(status_code=403, detail="Only admins can set user roles")
        current_user_company_id = current_user.company_id
        current_user_company = get_company_by_id(db=db, company_id=current_user_company_id)
        if not current_user_company:
            raise HTTPException(status_code=404, detail="Current user's company not found")
        
        body = await request.json()
        user_id = body.get("user_id")
        new_role = body.get("role")

        if not user_id or not new_role:
            raise HTTPException(status_code=400, detail="user_id and role are required fields")
        
        # only two roles are allowed
        if new_role not in ["admin", "member"]:
            raise HTTPException(status_code=400, detail="Invalid role")

        user = get_one_user_id(db=db, user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found in the database")

        old_role = user.user_type
        # no repeat role assignment
        if old_role == new_role:
            raise HTTPException(status_code=400, detail=f"User is already a {new_role}") 
        
         # update user role
        user.user_type = new_role
       
        if old_role == "admin":
            current_user_company.admin_count -= 1
            current_user_company.member_count += 1
        elif old_role == "member":
            current_user_company.admin_count += 1
            current_user_company.member_count -= 1
        
   
        

     
        db.commit()

        return JSONResponse(
            content={"message": f"User role updated from {old_role} to {new_role}", "success": True},
            status_code=200
        )
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
    
@router.post("/change-user-photo")
async def change_user_photo(file: UploadFile = File(...), db: Session = Depends(get_db), request: Request = None):
    """
    Changes the user photo uploaded by a user stores it in cloud storage,
    and removes the old photo if it exists.
    Args:
        file: The uploaded image file.
        request: The request object containing the user token.
    Returns:
        dict: A JSON response with a success message and the new photo URL.
    
    Example Response:
        {
            "message": "User photo successfully updated for {user_id}",
            "photo_url": "https://storage.googleapis.com/your-bucket-name/user_photos/photo_123456.jpg"
        }
    """
    # Auth part, get the current user
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header is missing")
    id_token = auth_header.split(" ")[1]
    decoded_token = auth.verify_id_token(id_token)
    current_user_id = decoded_token.get("uid")
    # Get the current user from the database
    current_user = db.query(Users).filter(Users.id == current_user_id).first()
    if not current_user:
        raise HTTPException(status_code=400, detail="Current user not found")
    try:
        if current_user.user_photo_url:
            try:
                old_blob_name = current_user.user_photo_url.split("/")[-1]
                old_blob = bucket.blob(f"user_photos/{current_user_id}/{old_blob_name}")
                old_blob.delete()
            except Exception as e:
                print(f"Error deleting old photo: {str(e)}")
                # We'll continue even if deletion fails
        # Generate a unique filename
        file_extension = os.path.splitext(file.filename)[1]
        new_filename = f"user_photos/{current_user_id}/photo_{uuid4()}{file_extension}"
        # Upload the file to Google Cloud Storage
        blob = bucket.blob(new_filename)
        blob.upload_from_file(file.file)
        # Make the blob publicly accessible
        blob.make_public()
        # Get the public URL
        photo_url = blob.public_url
        # Update the user's photo URL in the database
        update_user_photo(db=db, user_id=current_user_id, photo_url=photo_url)
        return JSONResponse(
            content={
                "message": f"User photo successfully updated for {current_user_id}",
                "photo_url": photo_url
            },
            status_code=200
    )
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
    
@router.post("/change-first-and-last-name")
async def change_first_and_last_name(data: UpdateFirstAndLastNameSchema, db: Session = Depends(get_db), request: Request = None):
    """
    Changes the user's first and last name
    Args:
        request: The request object containing the user token.
    Returns:
        dict: A JSON response with a success message
    Example Response:
        {
            "message": "User first and last name updated for {user_id}",
        }
    Request Body:
        {
            "first_name": "first_name",
            "last_name": "last_name",
            "mobile_number": "mobile_number
        }
  """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header is missing")
        id_token = auth_header.split(" ")[1]
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token.get("uid")

        # retrieve the user from the database using the user_id parameter
        user = get_one_user_id(db=db, user_id=user_id)  
        if not user:
            raise HTTPException(status_code=404, detail="User not found in the database")

        # get the current user from the database
        current_user = db.query(Users).filter(Users.id == user_id).first()
        if not current_user:
            raise HTTPException(status_code=400, detail="Current user not found")

        first_name = data.first_name
        last_name = data.last_name
        update_first_and_last_name(db=db, user_id=user_id, first_name=first_name, last_name=last_name)
        
        return JSONResponse(
        content={"message":  f"Account successfully updated for {user_id}"},
        status_code=200
        )
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))

@router.post("/resend-verification-link")
@limiter.limit("1/minute")  # Apply rate limiting
async def resend_verification_link(request: Request, data: ResendLinkSchema, db: db_dependency):
    """
    Endpoint to resend an email verification link to the user's email.

    Returns:
        dict: A JSON response with a success message.
    
    Example Response:
        {
            "success": True,
            "message": "Verification link sent to user_email"
        }
    
    Request Body:
        {
            "email": "user_email"
        }
    """
    user_email = data.email
    if not user_email:
        raise HTTPException(status_code=400, detail="Email is required")

    try:
        user = auth.get_user_by_email(user_email)
        if user.email_verified:
            return {"success": True, "message": "Email already verified."}

        verification_link = auth.generate_email_verification_link(user_email)
        await send_verification_email(user_email, verification_link)
        return {"success": True, "message": f"Verification link sent to {user_email}"}
    except auth.UserNotFoundError:
        raise HTTPException(status_code=404, detail="User with this email does not exist")
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
    
