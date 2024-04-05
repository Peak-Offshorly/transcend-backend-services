from uuid import UUID
from sqlalchemy.orm import Session
from app.database.models import TraitsQuestions

def traits_questions_get_all(db: Session):
    return db.query(TraitsQuestions).all()

def traits_questions_get_one(db: Session, id: UUID):
    return db.query(TraitsQuestions).filter_by(id=id).one()
