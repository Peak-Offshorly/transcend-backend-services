from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database.models import Practices, Questions, ChosenTraits
from app.schemas.models import PracticeSchema

async def practice_save_one(db: Session, practice: PracticeSchema):
    question_id = practice.question_id
    
    question = db.query(Questions).filter(Questions.id == question_id).first()
    chosen_trait = db.query(ChosenTraits).filter(ChosenTraits.form_id == question.form_id).first()
    new_practice = Practices(
        user_id=practice.user_id,
        chosen_traits_id=chosen_trait.id,
        name=question.name
    )

    db.add(new_practice)
    db.commit()

async def practices_by_trait_type_get(db: Session, user_id: str, trait_type: str):
    chosen_trait_id = db.query(ChosenTraits.id).filter(
        ChosenTraits.user_id == user_id,
        ChosenTraits.trait_type == trait_type
    ).scalar()

    practices = db.query(Practices).filter(
        Practices.chosen_trait_id == chosen_trait_id
    ).all()

    return practices


