from uuid import UUID
from sqlalchemy.orm import Session
from app.database.models import Accounts

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