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

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/company", tags=["company"])

@router.post("/create-company", response_model=CompanyDataSchema)
async def create_company_endpoint(data: CompanyDataSchema, db: db_dependency):
    try:
        company = create_company(db=db, company=data)
        
        # convert UUID to string 
        company_dict = {
            "id": str(company.id),
            "name": company.name,
            "seats": company.seats
        }
        company_data = CompanyDataSchema(**company_dict)

        return JSONResponse(content={"company": company_data.dict()}, status_code=201)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
    
@router.get("/get-company/{company_id}", response_model=CompanyDataSchema)
async def get_company_endpoint(company_id: str, db: db_dependency):
    try:
        company = get_company_by_id(db=db, company_id=company_id)

        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")

        # Convert SQLAlchemy model instance to Pydantic schema and ensure the id is a string
        company_data = CompanyDataSchema(
            id=str(company.id),  # Convert UUID to string
            name=company.name,
        )

        return company_data
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))