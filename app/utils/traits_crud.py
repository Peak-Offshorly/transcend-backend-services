import json
from uuid import UUID
from sqlalchemy import func, asc, desc
from sqlalchemy.orm import Session
from app.database.models import Traits, ChosenTraits
from app.schemas.models import InitialAnswerSchema

# Creates set of Traits for a new User
def traits_create(db: Session, user_id: str):
    if db.query(Traits).filter(Traits.user_id == user_id).count() == 18:
        return "User competencies already exist"
    
    with open("app/utils/data/traits.json", "r") as traits_json:
        traits_data = json.load(traits_json)
    
    trait_ids_names = []

    for name, avg, std in zip(traits_data["traits"], traits_data["traits_avg"], traits_data["traits_std"]):
        db_trait = Traits(user_id=user_id, name=name, average=avg, standard_deviation=std)
        db.add(db_trait)
        db.flush()
        trait_ids_names.append((str(db_trait.id), db_trait.name))

    db.commit()
    return trait_ids_names

# Compute T-Score for user Traits: used in Post Save Initial Answers endpoint
# Formula: (Count of Traits Choice - Avg)/Stdev*10+50
def traits_compute_tscore(db: Session, answers: InitialAnswerSchema):
    user_id = answers.user_id
    user_traits = db.query(Traits).filter(Traits.user_id == user_id).all()

    if user_traits:
        for trait in user_traits:
            trait.t_score = (func.coalesce(Traits.total_raw_score, 0) - trait.average)/trait.standard_deviation * 10 + 50

    db.commit()

    return { "message": "T-scores computed." }

def traits_get_top_bottom_five(db: Session, user_id: str):
    top_user_traits = db.query(Traits).filter(Traits.user_id == user_id).order_by(desc(Traits.t_score)).limit(5).all()
    bottom_user_traits = db.query(Traits).filter(Traits.user_id == user_id).order_by(asc(Traits.t_score)).limit(5).all()
    
    return {
        "user_id": user_id,

        "strengths": [{
            "name": trait.name,
            "t_score": trait.t_score
        } for trait in top_user_traits],
        
        "weaknesses": [{
            "name": trait.name,
            "t_score": trait.t_score
        } for trait in bottom_user_traits]
    }

def chosen_traits_create(db: Session, user_id: str):
    return None

def chosen_traits_get(db: Session, user_id: str):
    return None

def traits_get_all(db: Session):
    return db.query(Traits).all()

def traits_get_one(db: Session, id: UUID):
    return db.query(Traits).filter_by(id=id).one()