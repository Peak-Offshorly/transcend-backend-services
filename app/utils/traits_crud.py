import json
from uuid import UUID
from sqlalchemy import func, asc, desc
from sqlalchemy.orm import Session
from app.database.models import Traits, ChosenTraits
from app.schemas.models import TraitsSchema, FormAnswerSchema, ChosenTraitsSchema

# Creates set of Traits for a new User
def traits_create(db: Session, user_id: str):
    if db.query(Traits).filter(Traits.user_id == user_id).count() == 18:
        return "User competencies already exist"
    
    with open("app/utils/data/traits.json", "r") as traits_json:
        traits_data = json.load(traits_json)
    
    trait_ids_names = []

    for name, avg, std in zip(traits_data["traits"], traits_data["traits_avg"], traits_data["traits_std"]):
        db_trait = Traits(
            user_id=user_id, 
            name=name, 
            average=avg, 
            standard_deviation=std
        )
        db.add(db_trait)
        db.flush()
        trait_ids_names.append((str(db_trait.id), db_trait.name))

    db.commit()
    return trait_ids_names

# Compute T-Score for user Traits: used in Post Save Initial Answers endpoint
# Formula: (Count of Traits Choice - Avg)/Stdev*10+50
def traits_compute_tscore(db: Session, answers: FormAnswerSchema):
    user_id = answers.user_id
    user_traits = db.query(Traits).filter(Traits.user_id == user_id).all()

    if user_traits:
        for trait in user_traits:
            trait.t_score = (func.coalesce(Traits.total_raw_score, 0) - trait.average)/trait.standard_deviation * 10 + 50

    db.commit()

def traits_get_top_bottom_five(db: Session, user_id: str):
    top_user_traits = db.query(Traits).filter(Traits.user_id == user_id).order_by(desc(Traits.t_score)).limit(5).all()
    bottom_user_traits = db.query(Traits).filter(Traits.user_id == user_id).order_by(asc(Traits.t_score)).limit(5).all()
    
    return {
        "user_id": user_id,

        "strengths": [{
            "id": trait.id,
            "name": trait.name,
            "t_score": trait.t_score
        } for trait in top_user_traits],
        
        "weaknesses": [{
            "id": trait.id,
            "name": trait.name,
            "t_score": trait.t_score
        } for trait in bottom_user_traits]
    }

def chosen_traits_create(db: Session, user_id: str, trait_id: str, trait_name: str, trait_type: str, t_score: int, form_id: str):
    # Create ChosenTrait entry
    chosen_trait = ChosenTraits(
        user_id=user_id,
        name=trait_name,
        trait_id=trait_id,
        trait_type=trait_type.upper(),
        form_id=form_id,
        t_score=t_score
    )
    db.add(chosen_trait)
    db.flush()

    db.commit()

def chosen_traits_get(db: Session, user_id: str):
    user_strength = db.query(ChosenTraits).filter(
        ChosenTraits.user_id == user_id,
        ChosenTraits.trait_type == "STRENGTH"
        ).first()
    
    user_weakness = db.query(ChosenTraits).filter(
        ChosenTraits.user_id == user_id,
        ChosenTraits.trait_type == "WEAKNESS"
        ).first()
    
    return {
        "user_id": user_id,
        "chosen_strength": {
            "name": user_strength.name,
            "start_date": user_strength.start_date,
            "end_date": user_strength.end_date
        },
        "chosen_weakness": {
            "name": user_weakness.name,
            "start_date": user_weakness.start_date,
            "end_date": user_weakness.end_date
        }
    }
