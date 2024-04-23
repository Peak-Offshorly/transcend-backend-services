from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.database.models import Answers, Traits


async def answers_to_initial_questions_save(db: Session, answers: dict):
    form_id = answers.get("id")
    user_id = answers.get("user_id")
    
    for answer in answers.get("answers", []):
        new_answer = Answers(
            form_id=form_id,
            question_id=answer["question_id"],
            option_id=answer["option_id"],
            answer=answer["answer"]
        )

        # Add Answer entry to db
        db.add(new_answer)

        # Increment user Trait total_raw_score by 1
        answer_trait_name = answer["trait_name"]
        user_trait = db.query(Traits).filter(
            Traits.name == answer_trait_name,
            Traits.user_id == user_id
        ).first()

        if user_trait:
            user_trait.total_raw_score = func.coalesce(Traits.total_raw_score, 0) + 1
            db.flush()
        
    db.commit()
    return { "message": "Initial question answers saved." }