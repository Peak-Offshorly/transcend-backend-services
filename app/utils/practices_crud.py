from uuid import UUID
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database.models import Practices, Questions, ChosenTraits, ChosenPractices, PersonalPracticeCategory, ChosenPersonalPractices
from app.schemas.models import PracticeSchema

async def practice_save_one(db: Session, practice: PracticeSchema):
    question_id = practice.question_id
    question = db.query(Questions).filter(Questions.id == question_id).first()
    chosen_trait = db.query(ChosenTraits).filter(ChosenTraits.form_id == question.form_id).first()
    new_practice = Practices(
        user_id=practice.user_id,
        chosen_trait_id=chosen_trait.id,
        name=question.name
    )

    db.add(new_practice)
    db.commit()

async def practices_clear_existing(db: Session, question_id: str, user_id: str):
    question = db.query(Questions).filter(Questions.id == question_id).first()
    chosen_trait = db.query(ChosenTraits).filter(ChosenTraits.form_id == question.form_id).first()

    existing_practices = db.query(Practices).filter(
        Practices.user_id == user_id,
        Practices.chosen_trait_id == chosen_trait.id
    ).all()

    if len(existing_practices) == 5:
        for existing_practice in existing_practices:
            db.delete(existing_practice)
            db.flush()

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

def chosen_practices_save_one(db: Session, user_id: str, name: str, practice_id: str, chosen_trait_id: str, form_id: str, sprint_number: int, sprint_id: UUID):
    # check if user has existing chosen practices with same sprint id
    existing_chosen_practice = db.query(ChosenPractices).filter(
        ChosenPractices.user_id == user_id,
        ChosenPractices.chosen_trait_id == chosen_trait_id,
        ChosenPractices.sprint_id == sprint_id,
    ).first()

    if existing_chosen_practice:
        existing_chosen_practice.name = name
        existing_chosen_practice.practice_id = practice_id
        existing_chosen_practice.chosen_trait_id = chosen_trait_id
        existing_chosen_practice.form_id = form_id
    else:
        chosen_practice = ChosenPractices(
            user_id=user_id,
            name=name,
            practice_id=practice_id,
            chosen_trait_id=chosen_trait_id,
            form_id=form_id,
            sprint_number=sprint_number,
            sprint_id=sprint_id
        )
        db.add(chosen_practice)
        db.flush()

    db.commit()   

async def personal_practice_category_save_one(db: Session, user_id: str, name: str):
    # check if user already has an existing category 
    existing_category = db.query(PersonalPracticeCategory).filter(
        PersonalPracticeCategory.user_id == user_id
    ).first()

    if existing_category:
        existing_category.name = name
    else:
        recommended_category = PersonalPracticeCategory(
            user_id=user_id,
            name=name
        )
        
        db.add(recommended_category)
        db.flush()

    db.commit()

async def personal_practice_category_get_one(db: Session, user_id: str):
    return db.query(PersonalPracticeCategory).filter(
        PersonalPracticeCategory.user_id == user_id
    ).first()

async def chosen_personal_practices_clear_existing(db: Session, user_id: str, recommended_mind_body_category_id: str):
    # check existing 
    existing_chosen_practices = db.query(ChosenPersonalPractices).filter(
        ChosenPersonalPractices.user_id == user_id,
        ChosenPersonalPractices.personal_practice_category_id == recommended_mind_body_category_id
    ).all()

    if existing_chosen_practices:
        for practice in existing_chosen_practices:
            db.delete(practice)
            db.flush()

    db.commit()

async def chosen_personal_practices_save_one(db: Session, user_id: str, name: str, recommended_mind_body_category_id: str):
    new_personal_practice = ChosenPersonalPractices(
        user_id=user_id,
        name=name,
        personal_practice_category_id=recommended_mind_body_category_id
    )

    db.add(new_personal_practice)
    db.commit()

async def chosen_personal_practices_get_all(db: Session, user_id: str, recommended_mind_body_category_id: str):
    return db.query(ChosenPersonalPractices).filter(
        ChosenPersonalPractices.user_id == user_id
    ).all()