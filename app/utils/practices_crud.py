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

def chosen_practices_save_one(db: Session, user_id: str, name: str, practice_id: str, chosen_trait_id: str, form_id: str, sprint_number: int):
    #TO ADD(?): checker for sprint para di magduplicate

    chosen_practice = ChosenPractices(
        user_id=user_id,
        name=name,
        practice_id=practice_id,
        chosen_trait_id=chosen_trait_id,
        form_id=form_id,
        sprint_number=sprint_number
    )
    db.add(chosen_practice)
    db.flush()

    db.commit()
    

async def chosen_practices_get_max_sprint(db: Session, user_id: str):
    # get max sprint number, if there are two of the max iterate by 1 the max sprint
    max_sprint = db.query(func.max(ChosenPractices.sprint_number)).filter(
        ChosenPractices.user_id == user_id
    ).scalar()

    if max_sprint is None:
        return None
    
    max_sprint_count = db.query(ChosenPractices).filter(ChosenPractices.sprint_number == max_sprint).count()
    if max_sprint_count == 2:
        return max_sprint + 1
    
    return max_sprint

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