from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.models import Users, Forms, Traits, ChosenTraits, Questions, Options, Answers, Practices, DevelopmentPlan, Sprints, Company
from app.schemas.models import UserCompanyDetailsSchema

def update_user_company_details(db: Session, user_id: str, company_size: int, industry: str, role: str, role_description: str):
    db_user = db.query(Users).filter(Users.id == user_id).first()
    
    if db_user:
        db_user.company_size = company_size
        db_user.industry = industry
        db_user.role = role
        db_user.role_description = role_description
        db.commit()

    return db_user

def get_user_company_details(db: Session, user_id: str):
    db_account = db.query(Users).filter(Users.id == user_id).first()

    if db_account:
        return UserCompanyDetailsSchema.model_validate(db_account)
    return None

async def get_all_users(db: Session) -> Users:
    return db.query(Users).all()

# Gets one account based from email; returns Account object if it exists
def get_one_user(db: Session, email: str):
    db_account = db.query(Users).filter(Users.email == email).first()

    if db_account:
        return db_account
    return None

# Gets one account based from user_id; returns Users object if it exists
def get_one_user_id(db: Session, user_id: str):
    db_account = db.query(Users).filter(Users.id == user_id).first()

    if db_account:
        return db_account
    return None

def create_user(db: Session, user: Users):
    db_user = Users(
        id = user.id,
        email = user.email,
        first_name = user.first_name,
        last_name = user.last_name,
        mobile_number = user.mobile_number,
        acc_activated = user.acc_activated,
        user_type = user.user_type,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

def update_user(db: Session, user_id=None, email=None, first_name=None, last_name=None):
    db_user = db.query(Users).filter(Users.id == user_id).first()

    if db_user:
        if email is not None and email.strip():
            db_user.email = email
        if first_name is not None and first_name.strip():
            db_user.first_name = first_name
        if last_name is not None and last_name.strip():
            db_user.last_name = last_name
        db.commit()

    return db_user

def delete_user(db: Session, user_id):
    db_user = db.query(Users).filter(Users.id == user_id).first()
    
    # Query all related entries for the user
    # Query all Forms except initial questions form
    if db_user:
        forms = db.query(Forms).filter(Forms.user_id == db_user.id, Forms.name != '1_INITIAL_QUESTIONS').all()
        for form in forms:
            questions = db.query(Questions).filter(Questions.form_id == form.id).all()
            for question in questions:
                options = db.query(Options).filter(Options.question_id == question.id).all()
                answers = db.query(Answers).filter(Answers.form_id == form.id, Answers.question_id == question.id).all()
                for option, answer in zip(options, answers):
                    db.delete(answer)
                    db.delete(option)
                
                db.delete(question)
            db.delete(form)

        chosen_traits = db.query(ChosenTraits).filter(ChosenTraits.user_id == db_user.id).all()
        for chosen_trait in chosen_traits:
            practices = db.query(Practices).filter(Practices.id == chosen_trait.practice_id).all()
            for practice in practices:
                db.delete(practice)
                db.delete(chosen_trait)

        traits = db.query(Traits).filter(Traits.user_id == db_user.id).all()
        development_plans = db.query(DevelopmentPlan).filter(DevelopmentPlan.user_id == db_user.id).all()
        for trait in traits:
            db.delete(trait)
        for dp in development_plans:
            db.delete(dp)
    
        db.delete(db_user)
        db.commit()

        return True
    
    return False

def get_all_user_dashboard(db: Session, company_id: str):
    result = db.execute(
        select(
            Users.first_name,
            Users.last_name,
            Users.email,
            Users.role,
            Sprints.number,
            Users.company_id,
            Users.id,
            Users.user_type,
            Users.user_photo_url
        )
        .join(Sprints, Users.id == Sprints.user_id, isouter=True)  
        .where(Users.company_id == company_id)
    )
    
    users_dict = {}
    for row in result.all():
        user_id = row.id
        sprint_number = row.number  # this will be None if the user has no associated sprint

        first_name = row.first_name if row.first_name is not None else None
        last_name = row.last_name if row.last_name is not None else None
        user_info = {
            "first_name": first_name,
            "last_name": last_name,
            "email": row.email,
            "role": row.role,
            "sprint_number": sprint_number,
            "company_id": row.company_id,
            "user_id": user_id,
            "user_type": row.user_type,
            "user_photo_url": row.user_photo_url
        }
        
        # add user to the dictionary if not already added or if this sprint number is more recent
        if user_id not in users_dict or (sprint_number is not None and (users_dict[user_id]["sprint_number"] is None or sprint_number > users_dict[user_id]["sprint_number"])):
            users_dict[user_id] = user_info
    
    return list(users_dict.values())

def add_user_to_company_crud(db: Session, user_id: str, company_id: str):
    db_user = db.query(Users).filter(Users.id == user_id).first()
    db_company = db.query(Company).filter(Company.id == company_id).first()

    if db_user and db_company:
        db_user.company_id = db_company.id
        db.commit()
        db.refresh(db_user)  

    return db_user

def create_user_in_dashboard(db: Session, user: Users):
    db_user = Users(
        id = user.id,
        email = user.email,
        acc_activated = user.acc_activated,
        company_id = user.company_id,
        user_type = user.user_type

    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

def get_latest_sprint_for_user(db: Session, user_id: str):
    
    result = db.execute(
        select(Sprints.number)
        .where(Sprints.user_id == user_id)
        .order_by(Sprints.number.desc())
        .limit(1)
    ).first()

    latest_sprint_number = result[0] if result else None
    return latest_sprint_number

def update_personal_details(db: Session, user_id=None, first_name=None, last_name=None, mobile_number=None, job_title=None):
    db_user = db.query(Users).filter(Users.id == user_id).first()

    if db_user:
        if first_name is not None and first_name.strip():
            db_user.first_name = first_name
        if last_name is not None and last_name.strip():
            db_user.last_name = last_name
        if mobile_number is not None and mobile_number.strip():
            db_user.mobile_number = mobile_number
        if job_title is not None and job_title.strip():
            db_user.role = job_title
        db.commit()

    return db_user

def update_user_photo(db: Session, user_id: str, photo_url: str):
    db_user = db.query(Users).filter(Users.id == user_id).first()

    if db_user:
        db_user.user_photo_url = photo_url
        db.commit()

    return db_user

def update_first_and_last_name(db: Session, user_id=None, first_name=None, last_name=None):
    db_user = db.query(Users).filter(Users.id == user_id).first()

    if db_user:
        if first_name is not None and first_name.strip():
            db_user.first_name = first_name
        if last_name is not None and last_name.strip():
            db_user.last_name = last_name
        db.commit()

    return db_user