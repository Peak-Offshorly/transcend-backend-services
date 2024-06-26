from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.database.models import UserColleagues

async def colleague_email_save_one(db: Session, user_id: str, email: str, dev_plan_id: str):
    new_colleague_email = UserColleagues(
        email=email,
        user_id=user_id,
        development_plan_id=dev_plan_id
    )
    db.add(new_colleague_email)
    db.flush()
    
    db.commit()
    

async def user_colleagues_clear_all(db: Session, user_id: str, dev_plan_id: str):
    existing_colleagues = db.query(UserColleagues).filter(
        UserColleagues.user_id == user_id,
        UserColleagues.development_plan_id == dev_plan_id
    ).all()

    if existing_colleagues:
        for colleague in existing_colleagues:
            db.delete(colleague)
            db.flush()
    
    db.commit()

async def user_colleagues_add_dates(db: Session, user_id: str, dev_plan_id: str, week_5_date: datetime, week_9_date: datetime, week_12_date: datetime):
    existing_colleagues = db.query(UserColleagues).filter(
        UserColleagues.user_id == user_id,
        UserColleagues.development_plan_id == dev_plan_id
    ).all()
    
    if existing_colleagues:
        for colleague in existing_colleagues:
            colleague.week_5_date = week_5_date
            colleague.week_9_date = week_9_date
            colleague.week_12_date = week_12_date
            db.flush()

    db.commit()

async def user_colleagues_count(db: Session, user_id: str, dev_plan_id: str):
    existing_colleagues = db.query(UserColleagues).filter(
        UserColleagues.user_id == user_id,
        UserColleagues.development_plan_id == dev_plan_id
    ).all()

    if existing_colleagues:
        return len(existing_colleagues)
    return 0
    
async def user_colleagues_survey_completed(db: Session, user_id: str, dev_plan_id: str):
    existing_colleagues_survey_completed = db.query(UserColleagues).filter(
        UserColleagues.user_id == user_id,
        UserColleagues.development_plan_id == dev_plan_id,
        UserColleagues.survey_completed == True
    ).all()

    if existing_colleagues_survey_completed:
        return len(existing_colleagues_survey_completed)
    return 0

async def user_colleagues_get_all(db: Session, user_id: str, dev_plan_id: str):
    return db.query(UserColleagues).filter(
        UserColleagues.user_id == user_id,
        UserColleagues.development_plan_id == dev_plan_id
    ).all()

async def user_colleagues_get_one_survey_token(db: Session, survey_token: str):
    return db.query(UserColleagues).filter(
        UserColleagues.survey_token == survey_token
    ).first()

async def user_colleagues_get_dates(db: Session, user_id: str, dev_plan_id: str):
    existing_colleague = db.query(UserColleagues).filter(
        UserColleagues.user_id == user_id,
        UserColleagues.development_plan_id == dev_plan_id
    ).first()

    if existing_colleague:
        return{
            "week_5": existing_colleague.week_5_date,
            "week_9": existing_colleague.week_9_date,
            "week_12": existing_colleague.week_12_date,
        }
