from uuid import UUID
from sqlalchemy.orm import Session
from app.database.models import Traits

def traits_get_all(db: Session):
    return db.query(Traits).all()

def traits_get_one(db: Session, id: UUID):
    return db.query(Traits).filter_by(id=id).one()
