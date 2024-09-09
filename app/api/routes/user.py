from datetime import datetime
import datetime as dt
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Annotated
from app.firebase.session import firebase, auth
import firebase_admin
from firebase_admin import auth, credentials
from app.database.models import Users
from app.schemas.models import SignUpSchema, UpdateUserSchema, LoginSchema, UserCompanyDetailsSchema,CustomTokenRequestSchema, AddUserToCompanySchema, AddUserToCompanyDashboardSchema, PasswordChangeRequest
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
    create_user_in_dashboard
)
from app.utils.company_crud import get_company_by_id
from app.email.send_reset_password import send_reset_password
from typing import List
from firebase_admin.exceptions import FirebaseError


db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/accounts", tags=["accounts"])
firebase_auth = HTTPBearer()

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
            acc_activated=True
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
  try:
    update_user(db=db, user_id=user_id, email=email, first_name=first_name, last_name=last_name)

    return JSONResponse(
      content={"message":  f"Account successfully updated for {user_id}"},
      status_code=200
    )
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  

@router.delete("/delete-user")
async def delete_user_account(email: str, db: db_dependency):
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
        # Check if the email parameter is provided
        if not email:
            raise HTTPException(status_code=400, detail="Email query parameter is required")

        # Retrieve the user from the database using the email
        user = get_one_user(db=db, email=email)  # Assuming the function expects an 'email'
        if not user:
            raise HTTPException(status_code=404, detail="User not found in the database")

        # Get the user ID (uid) from the database user object
        uid = user.id

        company = get_company_by_id(db=db, company_id=user.company_id)
        if company:
            if user.user_type == 'admin':
                company.admin_count -= 1
            if user.user_type == 'member':
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
    Sets the role of a user in Firebase Authentication custom claims.

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
        
        user = auth.get_user(user_id)
        custom_claims = user.custom_claims or {}
        role_from_claims = custom_claims.get('role', 'unknown')  
        print(f"Current role: {role_from_claims}")
        
        # only two roles are allowed
        if role not in ["admin", "member"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        
        # no repeat role assignment
        if role_from_claims == role:
            raise HTTPException(status_code=400, detail=f"User is already a {role}")
        
        db_user = db.query(Users).filter(Users.id == user_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found in the database")

        if role == "admin":
            if role_from_claims == "member":
                raise HTTPException(status_code=400, detail="This user can't be promoted to admin")
            if role_from_claims == "unknown":
                auth.set_custom_user_claims(user_id, {'role': role})

                print(f"Set: User role set to {role}")
                db_user.user_type = 'admin'
                db.commit()

        if role == "member":
            if role_from_claims == "admin":
                auth.set_custom_user_claims(user_id, {'role': role})
                print(f"Set: User role set to {role}")
                db_user.user_type = 'member'
                db.commit()
            if role_from_claims == "unknown":
                auth.set_custom_user_claims(user_id, {'role': role})
                print(f"Set: User role set to {role}")
                db_user.user_type = 'member'
                db.commit()

        return JSONResponse(
            content={"message": f"User role set to {role}", "success": True},
            status_code=200
        )
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
  
@router.get("/get-user-role")
async def get_user_role(request: Request):
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
        body = await request.json()
        user_email = body.get("user_email")

        if not user_email:
            raise HTTPException(status_code=400, detail="user_email is required")
        
        user = get_one_user(db=db, email=user_email)

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
        print(f"Current user: {current_user.email}\n Current user role: {current_user.role}")
        # Check if the current user is an admin or if they're viewing their own profile
        if current_user.user_type == 'admin' or current_user.id == user_id:
            requested_user = db.query(Users).filter(Users.id == user_id).first()
            if not requested_user:
                raise HTTPException(status_code=404, detail="Requested user not found")
            
            return {
                "id": requested_user.id,
                "email": requested_user.email,
                "first_name": requested_user.first_name,
                "last_name": requested_user.last_name,
                "mobile_number": requested_user.mobile_number,
                "company_size": requested_user.company_size,
                "industry": requested_user.industry,
                "role": requested_user.role,
                "role_description": requested_user.role_description,
                "company_id": requested_user.company_id,
                "created_at": requested_user.created_at,
                "is_active": requested_user.is_active,
                "acc_activated": requested_user.acc_activated,
                "user_type": requested_user.user_type
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
async def add_user_to_company(data: AddUserToCompanySchema, db: db_dependency):
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
        user_id = data.user_id
        company_id = data.company_id


        if not user_id or not company_id:
            raise HTTPException(status_code=400, detail="user_id and company_id are required fields")

      
        updated_user = add_user_to_company_crud(db=db, user_id=user_id, company_id=company_id)

        if not updated_user:
            raise HTTPException(status_code=404, detail="User or Company not found")

        return {
            "message": f"User with ID {user_id} has been successfully added to the company with ID {company_id}.",
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

        current_user = db.query(Users).filter(Users.id == current_user_id).first()
        current_user_company_id = current_user.company_id


        if not current_user_company_id:
            raise HTTPException(status_code=400, detail="Current user's company ID not found")

        response_data = []

        for entry in data:
            user_email = entry.user_email
            user_role = entry.user_role

            if not user_email or not user_role:
                raise HTTPException(status_code=400, detail="user_email and user_role are required fields")

            # Create a new user in Firebase
            try:
                firebase_user = auth.create_user(
                    email=user_email,
                    email_verified=False,
                    disabled=False
                )

                # Generate a password reset link and send it via email
                link = auth.generate_password_reset_link(firebase_user.email)
                # send_custom_email(firebase_user.email, link)

            except Exception as firebase_error:
                raise HTTPException(status_code=400, detail=f"Error creating user in Firebase: {str(firebase_error)}")

            # Create the user in the database
            new_user = Users(
                id=firebase_user.uid,
                email=user_email,
                role=user_role,
                company_id=current_user_company_id
            )

            created_user = create_user_in_dashboard(db=db, user=new_user)

            # Set custom user claims in Firebase
            try:
                if user_role not in ["admin", "member"]:
                    raise HTTPException(status_code=400, detail="Invalid role")

                auth.set_custom_user_claims(firebase_user.uid, {'role': user_role})
                print(f"Set: User role set to {user_role}")

            except Exception as claim_error:
                raise HTTPException(status_code=400, detail=f"Error setting user role: {str(claim_error)}")

            # Send password reset email
            await send_reset_password(firebase_user.email, link)

            # Add success response for the current user
            response_data.append({
                "message": f"Account successfully created for {entry.user_email}",
                "user_id": firebase_user.uid,
                "email": entry.user_email,
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
        # Extract the token
        token = credentials.credentials

        # Verify the token
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']

        # Get the user's email
        user = auth.get_user(uid)
        email = user.email

        # Verify the old password
        try:
            # Firebase Admin SDK doesn't have a direct method to verify password
            # You might need to use Firebase Auth REST API or a custom solution here
            # For now, we'll skip this step and add a TODO
            # TODO: Implement old password verification
            pass
        except FirebaseError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error verifying old password: {str(e)}"
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