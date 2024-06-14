from uuid import UUID
from sqlalchemy.orm import Session
from app.database.models import Users, Forms, Traits, ChosenTraits, Questions, Options, Answers, Practices, DevelopmentPlan

def update_user_company_details(db: Session, user_id: str, company_size: int, industry: str, role: str, role_description: str):
    db_user = db.query(Users).filter(Users.id == user_id).first()
    
    if db_user:
        db_user.company_size = company_size
        db_user.industry = industry
        db_user.role = role
        db_user.role_description = role_description
        db.commit()

    return db_user

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
        last_name = user.last_name
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

def update_user(db: Session, user_id, first_name, last_name):
    db_user = db.query(Users).filter(Users.id == user_id).first()

    if db_user:
        db_user.first_name = first_name
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
