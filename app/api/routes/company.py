from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.models import Company, Users
from app.schemas.models import CompanyDataSchema
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
    get_org_growth_percentages)

from uuid import uuid4
from typing import Optional, List
from firebase_admin import auth, credentials

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