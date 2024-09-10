from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import select, func, case
from app.database.models import Users, Forms, Traits, ChosenTraits, Questions, Options, Answers, Practices, DevelopmentPlan, Sprints, Company, UserColleagues, UserColleaguesSurvey
from app.schemas.models import UserCompanyDetailsSchema
from datetime import date
from app.schemas.models import UserCompanyDetailsSchema, CompanyDataSchema

# function to create a new company
def create_company(db: Session, name: str, member_count: int, admin_count: int):
    existing_company = db.query(Company).filter(Company.name == name).first()
    if existing_company:
        return {"error": "A company with this name already exists."}

    db_company = Company(
        id=uuid4(),  
        name=name,
        member_count=member_count,
        admin_count=admin_count
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

def get_strengths_by_company_id(db: Session, company_id: str):
    company_strengths = db.query(
        Traits.name,
        func.count(Traits.id).label('employee_count')
    ).join(
        Users, Users.id == Traits.user_id
    ).join(
        ChosenTraits, ChosenTraits.trait_id == Traits.id
    ).filter(
        Users.company_id == company_id,
        ChosenTraits.trait_type == 'STRENGTH'
    ).group_by(
        Traits.name
    ).all()

    return {
        "strengths": [
            {
                "name": strength.name,
                "employee_count": strength.employee_count,
            } for strength in company_strengths
        ],
    }

def get_weakness_by_company_id(db: Session, company_id: str):
    company_weakness = db.query(
        Traits.name,
        func.count(Traits.id).label('employee_count')
    ).join(
        Users, Users.id == Traits.user_id
    ).join(
        ChosenTraits, ChosenTraits.trait_id == Traits.id
    ).filter(
        Users.company_id == company_id,
        ChosenTraits.trait_type == 'WEAKNESS'
    ).group_by(
        Traits.name
    ).all()

    return {
        "weakness": [
            {
                "name": weakness.name,
                "employee_count": weakness.employee_count,
            } for weakness in company_weakness
        ],
    }

def get_significant_strengths_weakness(db: Session, company_id: str):
    significant_strengths = db.query(
        Traits.name,
        func.count(Traits.id).label('employee_count')
    ).join(
        Users, Users.id == Traits.user_id
    ).join(
        ChosenTraits, ChosenTraits.trait_id == Traits.id
    ).filter(
        Users.company_id == company_id,
        ChosenTraits.trait_type == 'STRENGTH',
        ChosenTraits.end_date > date.today()
    ).group_by(
        Traits.name
    ).all()

    significant_weakness = db.query(
        Traits.name,
        func.count(Traits.id).label('employee_count')
    ).join(
        Users, Users.id == Traits.user_id
    ).join(
        ChosenTraits, ChosenTraits.trait_id == Traits.id
    ).filter(
        Users.company_id == company_id,
        ChosenTraits.trait_type == 'WEAKNESS',
        ChosenTraits.end_date > date.today()
    ).group_by(
        Traits.name
    ).all()

    return {
        "strengths": [
            {
                "name": strength.name,
                "employee_count": strength.employee_count,
            } for strength in significant_strengths
        ],
        "weakness": [
            {
                "name": weakness.name,
                "employee_count": weakness.employee_count,
            } for weakness in significant_weakness
        ]
    }

def get_org_growth_percentages(db: Session, company_id: str):
    employees = (
        select(
            UserColleagues.id,
            UserColleagues.email,
            Users.company_id
        )
        .join(Users, Users.id == UserColleagues.user_id)
        .where(Users.company_id == company_id)
        .cte('employees')
    )
    survey_data = (
        select(
            UserColleaguesSurvey.effective_leader,
            UserColleaguesSurvey.effective_strength_area,
            UserColleaguesSurvey.effective_weakness_area
        )
        .join(employees, employees.c.id == UserColleaguesSurvey.user_colleague_id)
        .cte('survey_data')
    )
    query = (
        select(
            (func.sum(case((survey_data.c.effective_leader > 0, 1), else_=0)) * 100.0 / func.count()).label('percent_effective_leader'),
            (func.sum(case((survey_data.c.effective_strength_area > 0, 1), else_=0)) * 100.0 / func.count()).label('percent_effective_strength_area'),
            (func.sum(case((survey_data.c.effective_weakness_area > 0, 1), else_=0)) * 100.0 / func.count()).label('percent_effective_weakness_area')
        )
        .select_from(survey_data)
    )

    result = db.execute(query).first()

    return {
        'percent_effective_leader': result.percent_effective_leader if result else None,
        'percent_effective_strength_area': result.percent_effective_strength_area if result else None,
        'percent_effective_weakness_area': result.percent_effective_weakness_area if result else None
    }