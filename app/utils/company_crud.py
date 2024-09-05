from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.models import Users, Forms, Traits, ChosenTraits, Questions, Options, Answers, Practices, DevelopmentPlan, Sprints, Company
from app.schemas.models import UserCompanyDetailsSchema, CompanyDataSchema

# function to create a new company
def create_company(db: Session, company: CompanyDataSchema):
    company_id = uuid4()
    existing_company = db.query(Company).filter(Company.name == company.name).first()
    
    if existing_company:
        return {"error": "A company with this name already exists."}
   
    db_company = Company(
        id=company_id, 
        name=company.name
    )

    db.add(db_company)
    db.commit()
    db.refresh(db_company)

    return db_company

# function to get details of a specific company by its ID
def get_company_by_id(db: Session, company_id: str):
    db_company = db.query(Company).filter(Company.id == company_id).first()

    if db_company:
        return db_company
    return None

def get_company_by_name(db: Session, company_name: str):
    db_company = db.query(Company).filter(Company.name == company_name).first()

    if db_company:
        return db_company
    return None

# function to get all companies
def get_all_companies(db: Session):
    return db.query(Company).all()

# function to update a company's details
def update_company(db: Session, company_id: str, name: str = None,):
    db_company = db.query(Company).filter(Company.id == company_id).first()

    if db_company:
        if name is not None and name.strip():
            company_new_id = uuid5(NAMESPACE_DNS, name)
            db_company.name = name
            db_company.id = company_new_id
        db.commit()
        db.refresh(db_company)

    return db_company

# function to delete a company by its ID
def delete_company(db: Session, company_id: str):
    db_company = db.query(Company).filter(Company.id == company_id).first()

    if db_company:
        db.delete(db_company)
        db.commit()
        return True
    
    return False