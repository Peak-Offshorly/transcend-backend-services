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