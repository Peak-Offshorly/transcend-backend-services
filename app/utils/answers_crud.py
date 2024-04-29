from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.database.models import Answers, Traits
from app.schemas.models import InitialAnswerSchema


async def answers_to_initial_questions_save(db: Session, answers: InitialAnswerSchema):
    form_id = answers.form_id
    user_id = answers.user_id
    
    # REVISION: user must be able to go back and change their answers
    # have a checker and see if that answer for that form_id and question_id already exist, 
    # and if it does, replace/update that answer entry 
    
    for answer in answers.answers:
        new_answer = Answers(
            form_id=form_id,
            question_id=answer.question_id,
            option_id=answer.option_id,
            answer=answer.answer
        )

        # Add Answer entry to db
        db.add(new_answer)

        # Increment user Trait total_raw_score by 1
        user_trait = db.query(Traits).filter(
            Traits.name == answer.trait_name,
            Traits.user_id == user_id
        ).first()

        if user_trait:
            user_trait.total_raw_score = func.coalesce(Traits.total_raw_score, 0) + 1
            db.flush()
        
    db.commit()
    return { "message": "Initial question answers saved." }

async def answers_to_trait_questions_save(db: Session, answers: InitialAnswerSchema):

    return { "message": "Strength/Weakness answers saved." }