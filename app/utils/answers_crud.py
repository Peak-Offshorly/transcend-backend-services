from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.database.models import Answers, Traits
from app.schemas.models import FormAnswerSchema


async def answers_to_initial_questions_save(db: Session, answers: FormAnswerSchema):
    form_id = answers.form_id
    user_id = answers.user_id
    
    # Reset to null the total raw score always to account for case of resubmission of initial answer Form
    user_traits = db.query(Traits).filter(Traits.user_id == user_id).all()
    for trait in user_traits:
        trait.total_raw_score = None
    db.flush()
    
    for answer in answers.answers:
        existing_answer = db.query(Answers).filter(
            Answers.form_id == form_id,
            Answers.question_id == answer.question_id
        ).first()
        
        # Check if answer already exists
        if existing_answer:
            existing_answer.option_id = answer.option_id
            existing_answer.answer = answer.answer
            
        else:
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

async def answers_save_one(db: Session, form_id: str, question_id: str, option_id: str, answer: str):
    # Check if answer already exists
    existing_answer = db.query(Answers).filter(
        Answers.form_id == form_id,
        Answers.question_id == question_id
    ).first()

    if existing_answer:
        # updates existing answer
        existing_answer.option_id = option_id
        existing_answer.answer = answer
    else:
        # adds a new Answer
        new_answer = Answers(
            form_id=form_id,
            question_id=question_id,
            option_id=option_id,
            answer=answer
        )
        # Add Answer entry to db
        db.add(new_answer)

    db.commit()