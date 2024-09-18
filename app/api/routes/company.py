from fastapi import APIRouter, Depends, HTTPException, status, Request, Body, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.models import Company, Users
from app.schemas.models import CompanyDataSchema, AddUserToCompanyDashboardSchema, CreateCompanyRequest
from app.database.connection import get_db
from app.utils.company_crud import (
    create_company, 
    get_company_by_id, 
    get_all_companies, 
    update_company, 
    delete_company,
    get_strengths_by_company_id,
    get_weakness_by_company_id,
    get_significant_strengths_weakness,
    get_org_growth_percentages,
    update_company_photo)

from app.utils.users_crud import (
    create_user_in_dashboard,
    get_one_user_id
)
from uuid import uuid4
from typing import Optional, List
from app.email.send_reset_password import send_reset_password
from firebase_admin import auth, credentials, storage
from firebase_admin.exceptions import FirebaseError
import os

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/company", tags=["company"])
bucket = storage.bucket()

@router.post("/create-company")
async def create_company_endpoint(
    request: Request,
    body: CreateCompanyRequest,
    db: db_dependency  
):
    """
    Creates a new company in the database and optionally adds multiple users to the company dashboard.
    """
    try:
        data = body.data
        users = body.users

        # auth part, get the current user
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header is missing")
        id_token = auth_header.split(" ")[1]
        decoded_token = auth.verify_id_token(id_token)
        current_user_id = decoded_token.get("uid")

        # get the current user from the database
        current_user = get_one_user_id(db=db, user_id=current_user_id)
        if not current_user:
            raise HTTPException(status_code=400, detail="Current user not found")

        # check if the current user is already associated with a company
        if current_user.company_id:
            raise HTTPException(status_code=400, detail="Current user is already associated with a company")

        # validate users data if provided
        if users:
            for entry in users:
                if not entry.user_email or not entry.user_role:
                    raise HTTPException(status_code=400, detail="user_email and user_role are required fields")
                if entry.user_role not in ["admin", "member"]:
                    raise HTTPException(status_code=400, detail="Invalid role. Role must be either 'admin' or 'member'.")

        # if all validations pass, proceed with company creation
        member_count = 0
        admin_count = 1  # assume the user creating the company is an admin

        # create the company in the database
        created_company = create_company(
            db=db, name=data.name, member_count=member_count, admin_count=admin_count
        )

        if isinstance(created_company, dict) and "error" in created_company:
            raise HTTPException(status_code=400, detail=created_company["error"])

        # for prompt
        company_data = CompanyDataSchema(
            id=str(created_company.id),
            name=created_company.name
        )

        response_content = {
            "company": company_data.dict(),
            "member_count": created_company.member_count,
            "admin_count": created_company.admin_count
        }

        # assign the current user to the company as an admin
        current_user.company_id = created_company.id
        current_user.user_type = "admin"

        # update the current user's company and role in the database
        db.commit()

        # set custom user claims in Firebase for current user
        try:
            auth.set_custom_user_claims(current_user_id, {'role': 'admin'})
        except Exception as claim_error:
            raise HTTPException(status_code=400, detail=f"Error setting user role for the current user: {str(claim_error)}")

        # optionally add additional users to the company 
        if users:
            response_data = []

            for entry in users:
                try:
                    firebase_user = auth.create_user(
                        email=entry.user_email,
                        email_verified=False,
                        disabled=False
                    )
                    
                    link = auth.generate_password_reset_link(firebase_user.email)

                    new_user = Users(
                        id=firebase_user.uid,
                        email=entry.user_email,
                        user_type=entry.user_role,
                        company_id=created_company.id  
                    )

                    db.add(new_user)
                    
                    # update the member or admin count 
                    if entry.user_role == "member":
                        created_company.member_count += 1
                    elif entry.user_role == "admin":
                        created_company.admin_count += 1

                    auth.set_custom_user_claims(firebase_user.uid, {'role': entry.user_role})

                    # send password reset email
                    await send_reset_password(firebase_user.email, link)

                    response_data.append({
                        "message": f"Account successfully created for {entry.user_email}",
                        "user_id": firebase_user.uid,
                        "email": entry.user_email,
                    })

                except Exception as user_error:
                    # if there's an error creating a user, we'll log it and continue
                    print(f"Error creating user {entry.user_email}: {str(user_error)}")
                    response_data.append({
                        "message": f"Error creating account for {entry.user_email}",
                        "error": str(user_error)
                    })

            # commit all changes after processing all users
            db.commit()

            response_content["member_count"] = created_company.member_count
            response_content["admin_count"] = created_company.admin_count
            response_content["members"] = response_data

        return JSONResponse(content=response_content, status_code=201)

    except HTTPException as http_error:
        # Re-raise HTTP exceptions
        raise http_error
    except Exception as error:
        # For any other exceptions, return a 400 Bad Request
        raise HTTPException(status_code=400, detail=str(error))
    
@router.get("/get-company/{company_id}")
async def get_company_endpoint(company_id: str, db: db_dependency):
    """
    Retrieves a specific company by its ID from the database.

    Args:
        company_id (str): The ID of the company to retrieve.
        db (Session): The database session dependency for performing the operation.

    Returns:
        CompanyDataSchema: The data of the requested company.

    Example Response:
        {
            "id": "be7d9689-3117-5819-9ffe-fa2b9ca205fb",
            "name": "Offshorly"
        }

    Input:
        Path Parameter:
            company_id (str): The ID of the company to be retrieved.
    """

    try:
        company = get_company_by_id(db=db, company_id=company_id)

        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company_data = CompanyDataSchema(
            id=str(company.id),  
            name=company.name,
        )

        return company_data
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))

@router.get("/employee-strengths")
async def get_employee_strengths_endpoint(request: Request, db: db_dependency):
  """
  Retrieves all the employee strengths of the company associated with the user token
  Args:
      request (Request): The request object containing the user token.
      db (Session): The database session dependency for performing the operation.
  Returns:
      dict: A dictionary containing two keys - company_id and strengths. The strengths key contains a list of dictionaries of traits with two keys - name and employee_count.
  Example Response:
  {
      "strengths": [
          {
              "name": "COACHING",
              "employee_count": 4
          },
          {
              "name": "DECISION MAKING",
              "employee_count": 2
          }
      ],
      "company_id": "c628c17c-ef36-5ce3-9b66-43c8f58402f6"
  }
  """
  try:
    # auth part, get the current user
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header is missing")
    id_token = auth_header.split(" ")[1]
    decoded_token = auth.verify_id_token(id_token)
    current_user_id = decoded_token.get("uid")

    # get the current user from the database
    current_user = db.query(Users).filter(Users.id == current_user_id).first()
    if not current_user:
        raise HTTPException(status_code=400, detail="Current user not found")

    if not current_user.company_id:
        raise HTTPException(status_code=404, detail="User is not associated with a company")

    company = get_company_by_id(db=db, company_id=current_user.company_id)

    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    
    response = get_strengths_by_company_id(db=db, company_id=current_user.company_id)
    response['company_id'] = current_user.company_id
    return response

  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
@router.get("/employee-weakness")
async def get_employee_weakness_endpoint(request: Request, db: db_dependency):
  """
  Retrieves all the employee weaknesses of the company associated with the user token
  Args:
      request (Request): The request object containing the user token.
      db (Session): The database session dependency for performing the operation.
  Returns:
      dict: A dictionary containing two keys - company_id and weakness. The weakness key contains a list of dictionaries of traits with two keys - name and employee_count.
  Example Response:
  {
      "weakness": [
          {
              "name": "COACHING",
              "employee_count": 4
          },
          {
              "name": "DECISION MAKING",
              "employee_count": 2
          }
      ],
      "company_id": "c628c17c-ef36-5ce3-9b66-43c8f58402f6"
  }
  """
  try:
    # auth part, get the current user
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header is missing")
    id_token = auth_header.split(" ")[1]
    decoded_token = auth.verify_id_token(id_token)
    current_user_id = decoded_token.get("uid")

    # get the current user from the database
    current_user = db.query(Users).filter(Users.id == current_user_id).first()
    if not current_user:
        raise HTTPException(status_code=400, detail="Current user not found")

    if not current_user.company_id:
        raise HTTPException(status_code=404, detail="User is not associated with a company")

    company = get_company_by_id(db=db, company_id=current_user.company_id)

    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    
    response = get_weakness_by_company_id(db=db, company_id=current_user.company_id)
    response['company_id'] = current_user.company_id
    return response
  
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
@router.get("/significant-strengths-weakness")
async def get_significant_strengths_weakness_endpoint(request: Request, db: db_dependency):
  """
  Retrieves all the current chosen traits of members of the company associated with the user token
  Args:
      request (Request): The request object containing the user token.
      db (Session): The database session dependency for performing the operation.
  Returns:
      dict: A dictionary containing three keys - company_id, strengths, and weaknesses. The strengths and weakness key contains a list of dictionaries of traits with two keys - name and employee_count.
  Example Response:
  {
      "strengths": [
          {
              "name": "COACHING",
              "employee_count": 3
          }
      ],
      "weakness": [
          {
              "name": "COACHING",
              "employee_count": 4
          },
          {
              "name": "DECISION MAKING",
              "employee_count": 2
          }
      ],
      "company_id": "c628c17c-ef36-5ce3-9b66-43c8f58402f6"
  }
  """
  try:
    # auth part, get the current user
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header is missing")
    id_token = auth_header.split(" ")[1]
    decoded_token = auth.verify_id_token(id_token)
    current_user_id = decoded_token.get("uid")

    # get the current user from the database
    current_user = db.query(Users).filter(Users.id == current_user_id).first()
    if not current_user:
        raise HTTPException(status_code=400, detail="Current user not found")

    if not current_user.company_id:
        raise HTTPException(status_code=404, detail="User is not associated with a company")

    company = get_company_by_id(db=db, company_id=current_user.company_id)

    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    
    response = get_significant_strengths_weakness(db=db, company_id=current_user.company_id)
    response['company_id'] = current_user.company_id
    return response
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

@router.get("/get-all-companies")
async def get_all_companies_endpoint(db: db_dependency):
    """
    Retrieves a list of all companies from the database.

    Args:
        db (Session): The database session dependency for performing the operation.

    Returns:
        list: A list of all companies in the database.

    Example Response:
        [
            {
                "id": "be7d9689-3117-5819-9ffe-fa2b9ca205fb",
                "name": "Offshorly"
            },
            {
                "id": "c628c17c-ef36-5ce3-9b66-43c8f58402f6",
                "name": "Peak"
            },
            {
                "id": "3a9e8927-239f-4939-ae7d-491b2fb18c7e",
                "name": "Nokia"
            }
        ]
    """

    try:
        companies = get_all_companies(db=db)
        return companies
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
    

@router.get("/get-company-number-of-members")
async def get_company_number_of_members_endpoint(
    request: Request,
    db: db_dependency
):
    """
    Retrieves the number of members in the company associated with the current user.

    Args:
        request (Request): The HTTP request object containing the necessary headers.
        db (Session): The database session dependency for performing the operation.
        
    Returns:
        dict: A JSON response with the number of members in the user's company.
    """
    try:
        # Extract the Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header is missing")

        # Verify the token and get the current user ID
        id_token = auth_header.split(" ")[1]
        decoded_token = auth.verify_id_token(id_token)
        current_user_id = decoded_token.get("uid")

        # Fetch the current user's details from the database
        current_user = get_one_user_id(db=db, user_id=current_user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get the user's type to ensure they have access
        current_user_user_type = current_user.user_type

        if current_user_user_type not in ["admin", "member"]:
            raise HTTPException(status_code=403, detail="User does not have permission to view member count")

        # Get the company ID from the current user's details
        current_user_company_id = current_user.company_id
        if not current_user_company_id:
            raise HTTPException(status_code=404, detail="User's company ID not found")

        # Retrieve the company details from the database
        company = get_company_by_id(db=db, company_id=current_user_company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Return the number of members in the company
        return {"member_count": company.member_count}

    except FirebaseError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Authentication error: {str(e)}"
        )
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
    
@router.get("/get-company-number-of-admins")
async def get_company_number_of_admins_endpoint(
    request: Request,
    db: db_dependency
):
    """
    Retrieves the number of admins in the company associated with the current user.

    Args:
        request (Request): The HTTP request object containing the necessary headers.
        db (Session): The database session dependency for performing the operation.
        
    Returns:
        dict: A JSON response with the number of admins in the user's company.
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
            raise HTTPException(status_code=404, detail="User not found")

        current_user_user_type = current_user.user_type

        if current_user_user_type != "admin":
            raise HTTPException(status_code=404, detail="User is not an admin")
        
        current_user_company_id = current_user.company_id

        if not current_user_company_id:
            raise HTTPException(status_code=404, detail="User's company ID not found")

  
        company = get_company_by_id(db=db, company_id=current_user_company_id)

        if not company:
            raise HTTPException(status_code=404, detail="Company not found")


        return {"admin_count": company.admin_count}

    except FirebaseError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Authentication error: {str(e)}"
        )
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
    
@router.get("/get-company-by-user-token")
async def get_company_by_user_token(request: Request, db: db_dependency):
    """
    Retrieves the company associated with the user token.

    Args:
        request (Request): The request object containing the user token.
        db (Session): The database session dependency for performing the operation.

    Returns:
        CompanyDataSchema: The data of the company associated with the user token.

    Example Response:
    {
        "company_id": "4259b944-db61-4780-99fb-2bec855f734a",
        "company_name": "Test Company"
    }
    """
    
    try:
        # auth part, get the current user
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header is missing")
        id_token = auth_header.split(" ")[1]
        decoded_token = auth.verify_id_token(id_token)
        current_user_id = decoded_token.get("uid")

        # get the current user from the database
        current_user = db.query(Users).filter(Users.id == current_user_id).first()
        if not current_user:
            raise HTTPException(status_code=400, detail="Current user not found")

        if not current_user.company_id:
            raise HTTPException(status_code=404, detail="User is not associated with a company")

        company = get_company_by_id(db=db, company_id=current_user.company_id)

        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")

        company_data = CompanyDataSchema(
            id=str(company.id),
            name=company.name,
            company_photo_url=company.company_photo_url
        )

        return {
            "company_id": company_data.id,
            "company_name": company_data.name,
            "company_photo_url": company_data.company_photo_url
        }
    except HTTPException as http_error:
  
        raise http_error
    except Exception as error:
  
        raise HTTPException(status_code=400, detail=str(error))

  
@router.get("/org-growth-percentages")
async def org_growth_percentages_endpoint(request: Request, db: db_dependency):
  """
  Retrieves the three percentage values in the organizational leadership growth index section
  Args:
      request (Request): The request object containing the user token.
      db (Session): The database session dependency for performing the operation.
  Returns:
      dict: A dictionary containing four keys - percent_effective_leader, percent_effective_strength_area, percent_effective_weakness_area, and company_id.
  Example Response:
  {
      "percent_effective_leader": 0.00000000000000000000,
      "percent_effective_strength_area": 33.3333333333333333,
      "percent_effective_weakness_area": 66.6666666666666667,
      "company_id": "c628c17c-ef36-5ce3-9b66-43c8f58402f6"
  }
  """
  try:
    # auth part, get the current user
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header is missing")
    id_token = auth_header.split(" ")[1]
    decoded_token = auth.verify_id_token(id_token)
    current_user_id = decoded_token.get("uid")

    # get the current user from the database
    current_user = db.query(Users).filter(Users.id == current_user_id).first()
    if not current_user:
        raise HTTPException(status_code=400, detail="Current user not found")

    if not current_user.company_id:
        raise HTTPException(status_code=404, detail="User is not associated with a company")

    company = get_company_by_id(db=db, company_id=current_user.company_id)

    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    
    response = get_org_growth_percentages(db=db, company_id=current_user.company_id)
    response['company_id'] = current_user.company_id
    return response
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
@router.post("/change-company-photo")
async def change_company_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Changes the company photo uploaded by a user and stores it in Firebase Storage
    Args:
        file: The uploaded image file.
        request: The request object containing the user token.
    Returns:
        dict: A JSON response with a success message and the new photo URL.
    
    Example Response:
        {
            "message": "Company photo successfully updated for {user_id}",
            "photo_url": "https://firebasestorage.googleapis.com/..."
        }
    """
    # Auth part, get the current user
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header is missing")
    id_token = auth_header.split(" ")[1]
    try:
        decoded_token = auth.verify_id_token(id_token)
        current_user_id = decoded_token['uid']
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    # Get the current user from the database
    current_user = db.query(Users).filter(Users.id == current_user_id).first()
    if not current_user:
        raise HTTPException(status_code=400, detail="Current user not found")

    try:
        # Generate a unique filename
        file_extension = os.path.splitext(file.filename)[1]
        new_filename = f"company_photos/{current_user_id}/photo_{uuid4()}{file_extension}"

        # Upload the file to Firebase Storage
        blob = bucket.blob(new_filename)
        blob.upload_from_file(file.file)

        # Make the blob publicly accessible
        blob.make_public()

        # Get the public URL
        photo_url = blob.public_url

        if not current_user.company_id:
            raise HTTPException(status_code=404, detail="User is not associated with a company")

        company = get_company_by_id(db=db, company_id=current_user.company_id)

        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")

        # Update the user's company photo URL in the database
        update_company_photo(db=db, company_id=current_user.company_id, photo_url=photo_url)

        return JSONResponse(
            content={
                "message": f"Company photo successfully updated for {current_user.company_id}",
                "photo_url": photo_url
            },
            status_code=200
        )
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))