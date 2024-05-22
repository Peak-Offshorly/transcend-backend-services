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

async def user_colleagues_get_all(db: Session, user_id: str, dev_plan_id: str):
    return db.query(UserColleagues).filter(
        UserColleagues.user_id == user_id
    ).all()
