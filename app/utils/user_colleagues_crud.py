from sqlalchemy.orm import Session
from app.database.models import UserColleagues

async def colleague_email_save_one(db: Session, user_id: str, email: str):
    existing_colleague_email = db.query(UserColleagues).filter(
        UserColleagues.user_id == user_id,
        UserColleagues.email == email
    ).all()

    if existing_colleague_email:
        return
    else:
        new_colleague_email = UserColleagues(
            email=email,
            user_id=user_id
        )

        db.add(new_colleague_email)
        db.flush()
    
    db.commit()

async def user_colleagues_get_all(db: Session, user_id: str):
    return db.query(UserColleagues).filter(
        UserColleagues.user_id == user_id
    ).all()
