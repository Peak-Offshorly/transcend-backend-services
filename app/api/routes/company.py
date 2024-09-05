from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.models import Company
from app.schemas.models import CompanyDataSchema
from app.database.connection import get_db
from app.utils.company_crud import (
    create_company, 
    get_company_by_id, 
    get_all_companies, 
    update_company, 
    delete_company)
from uuid import uuid4

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/company", tags=["company"])

@router.post("/create-company")
async def create_company_endpoint(data: CompanyDataSchema, db: db_dependency):
    """
    Creates a new company in the database.

    Args:
        data (CompanyDataSchema): The request data containing the details of the company to be created.
        db (Session): The database session dependency for performing the operation.

    Returns:
        JSONResponse: A JSON response with the created company's data.

    Example Response:
{
    "company": {
        "id": "dee1d2f4-fcba-4b26-b746-4d4d1c82b4b4",
        "name": "Adventure"
    },
    "member_count": 0,
    "admin_count": 1
}

    Request Body:
        {
            "name": "New Company"
        }
    
    """

    try:
        member_count = 0
        admin_count = 1  # assume the user creating the company is an admin

       
        created_company = create_company(db=db, name=data.name, member_count=member_count, admin_count=admin_count)

        if isinstance(created_company, dict) and "error" in created_company:
            raise HTTPException(status_code=400, detail=created_company["error"])

     
        company_data = CompanyDataSchema(
            id=str(created_company.id),  
            name=created_company.name
        )

        
        return JSONResponse(
            content={
                "company": company_data.dict()
            },
            status_code=201
        )

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
    

