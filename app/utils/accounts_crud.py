from uuid import UUID
from sqlalchemy.orm import Session
from app.database.models import Accounts

# Gets one account based from email; returns Account object if it exists
def get_one_account(db: Session, account_email):
    db_account = db.query(Accounts).filter(Accounts.email == account_email).first()

    if db_account:
        return db_account
    return None

def create_account(db: Session, account: Accounts):
    db_account = Accounts(
        id = account.id,
        email = account.email,
        password = account.password,
        first_name = account.first_name,
        last_name = account.last_name
    )

    db.add(db_account)
    db.commit()
    db.refresh(db_account)

    return db_account

def update_account(db: Session, account_id, first_name, last_name):
    db_account = db.query(Accounts).filter(Accounts.id == account_id).first()

    if db_account:
        db_account.first_name = first_name
        db_account.last_name = last_name
        db.commit()

    return db_account

def delete_account(db: Session, account_id):
    db_account = db.query(Accounts).filter(Accounts.id == account_id).first()

    if db_account:
        db.delete(db_account)
        db.commit()

        return True
    
    return False
