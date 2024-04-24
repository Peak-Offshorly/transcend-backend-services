from uuid import UUID
from sqlalchemy.orm import Session
from app.database.models import Users

# Gets one account based from email; returns Account object if it exists
def get_one_user(db: Session, email: str):
    db_account = db.query(Users).filter(Users.email == email).first()

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

    if db_user:
        db.delete(db_user)
        db.commit()

        return True
    
    return False
