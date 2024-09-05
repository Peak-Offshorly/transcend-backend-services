from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
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
    delete_company)

from app.utils.users_crud import (
    create_user_in_dashboard
)
from uuid import uuid4
from typing import Optional, List
from app.email.send_reset_password import send_reset_password
from firebase_admin import auth, credentials

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/company", tags=["company"])

@router.post("/create-company")
async def create_company_endpoint(
    request: Request,
    body: CreateCompanyRequest,  # Use the combined model for the request body
    db: db_dependency  
):
    """
    Creates a new company in the database and optionally adds multiple users to the company dashboard.
    """
    try:
        #extracting data
        data = body.data
        users = body.users

        # initial number of a company
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

        # content of the response
        response_content = {
            "company": company_data.dict(),
            "member_count": created_company.member_count,
            "admin_count": created_company.admin_count
        }

        # authorization part, get the current user
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
        # check if the current user is already have company
        if current_user.company_id:
            raise HTTPException(status_code=400, detail="Current user is already associated with a company")
        # assign the current user to the company as an admin
        current_user.company_id = created_company.id
        current_user.user_type = "admin"

        # update the current user's company and role in the database
        db.commit()

        # custom user claims in Firebase 
        try:
            auth.set_custom_user_claims(current_user_id, {'role': 'admin'})
        except Exception as claim_error:
            raise HTTPException(status_code=400, detail=f"Error setting user role for the current user: {str(claim_error)}")

        # optionally add additional users to the company 
        if users:
            response_data = []

            # iterate over the provided users 
            for entry in users:
                user_email = entry.user_email
                user_role = entry.user_role

                if not user_email or not user_role:
                    raise HTTPException(status_code=400, detail="user_email and user_role are required fields")

                try:
                    firebase_user = auth.create_user(
                        email=user_email,
                        email_verified=False,
                        disabled=False
                    )

                    
                    link = auth.generate_password_reset_link(firebase_user.email)
                    

                except Exception as firebase_error:
                    raise HTTPException(status_code=400, detail=f"Error creating user in Firebase: {str(firebase_error)}")

                new_user = Users(
                    id=firebase_user.uid,
                    email=user_email,
                    user_type=user_role,
                    company_id=created_company.id  
                )

                db.add(new_user)  
                db.commit()  

                # update the member or admin count 
                if user_role == "user":
                    created_company.member_count += 1
                elif user_role == "admin":
                    created_company.admin_count += 1

                # commit the updated counts to the database
                db.commit()

                # custom user claims in Firebase
                try:
                    if user_role not in ["admin", "user"]:
                        raise HTTPException(status_code=400, detail="Invalid role")

                    auth.set_custom_user_claims(firebase_user.uid, {'role': user_role})

                except Exception as claim_error:
                    raise HTTPException(status_code=400, detail=f"Error setting user role: {str(claim_error)}")

                # send password reset email
                await send_reset_password(firebase_user.email, link)

              
                response_data.append({
                    "message": f"Account successfully created for {entry.user_email}",
                    "user_id": firebase_user.uid,
                    "email": entry.user_email,
                })

        
            response_content["member_count"] = created_company.member_count
            response_content["admin_count"] = created_company.admin_count
            response_content["users"] = response_data

        return JSONResponse(content=response_content, status_code=201)

    except Exception as error:
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
    

