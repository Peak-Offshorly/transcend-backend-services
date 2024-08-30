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