from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.database.models import Answers, Traits, Forms
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

async def answers_clear_all(db: Session, form_id: str):
    existing_answers = db.query(Answers).filter(
        Answers.form_id == form_id
    ).all()

    if existing_answers:
        for answer in existing_answers:
            db.delete(answer)
            db.flush()

    db.commit()

async def answers_get_all(db: Session, user_id: str, form_name: str, sprint_number: str, dev_plan_id: str):
    form = db.query(Forms).filter(
        Forms.user_id == user_id, 
        Forms.name == form_name, 
        Forms.sprint_number == sprint_number,
        Forms.development_plan_id == dev_plan_id
        ).options(joinedload(Forms.answers)).first()
    
    if form:
        return form.answers
    return None

async def answers_all_forms_get_all(db: Session, user_id: str, dev_plan_id: str):
    all_forms_with_answers = db.query(Forms).filter(
        Forms.user_id == user_id,
        Forms.development_plan_id == dev_plan_id
    ).options(joinedload(Forms.answers)).all()

    return all_forms_with_answers

async def initial_questions_answers_all_forms_get_all(db: Session, user_id: str):
    all_forms_with_answers = db.query(Forms).filter(
        Forms.user_id == user_id,
        Forms.name == "1_INITIAL_QUESTIONS"
    ).options(joinedload(Forms.answers)).all()

    return all_forms_with_answers


'''
Checks if new answers match existing answers

If answers do not exist for a form
Returns None

Otherwise
Returns True/False
'''
async def are_matching_answers(db: Session, user_id: str, form_name: str, sprint_number: str, dev_plan_id: str, new_answers):
    existing_answers = await answers_get_all(db=db, user_id=user_id, form_name=form_name, sprint_number=sprint_number, dev_plan_id=dev_plan_id)
    if existing_answers:
        existing_answers_dict = {
            str(answer.question_id): answer.answer for answer in existing_answers
        }
        new_answers_dict = {
            str(answer.question_id): answer.answer for answer in new_answers
        }
        return existing_answers_dict == new_answers_dict

    return None