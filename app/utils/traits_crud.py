from uuid import UUID
from sqlalchemy.orm import Session
from app.database.models import Traits
from app.schemas.models import TraitsSchema
from app.const import TRAITS, TRAITS_AVG, TRAITS_STD

# Creates set of Traits for a new User
def traits_create(db: Session, user_id: str):

    if db.query(Traits).filter(Traits.user_id == user_id).count() == 18:
        return "User competencies already exist"
    
    trait_ids_names = []

    for name, avg, std in zip(TRAITS, TRAITS_AVG, TRAITS_STD):
        db_trait = Traits(user_id=user_id, name=name, average=avg, standard_deviation=std)
        db.add(db_trait)
        db.flush()
        trait_ids_names.append((str(db_trait.id), db_trait.name))

    db.commit()
    return trait_ids_names

def traits_get_all(db: Session):
    return db.query(Traits).all()

def traits_get_one(db: Session, id: UUID):
    return db.query(Traits).filter_by(id=id).one()
