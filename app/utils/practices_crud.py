import random
from uuid import UUID
from sqlalchemy import delete
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

async def practices_and_chosen_practices_clear_all(db: Session, chosen_strength_id: str, chosen_weakness_id: str, dev_plan_id: str, user_id: str):
    if (chosen_strength_id or chosen_weakness_id) == "": 
        return None

    # Delete CHOSEN strength and weakness practice
    db.execute(
        delete(ChosenPractices).where((
            ChosenPractices.chosen_trait_id == chosen_strength_id
    )))
    db.execute(
        delete(ChosenPractices).where((
            ChosenPractices.chosen_trait_id == chosen_weakness_id
    )))

    # Delete strength and weakness practices
    db.execute(
        delete(Practices).where((
            Practices.chosen_trait_id == chosen_strength_id
    )))
    db.execute(
        delete(Practices).where((
            Practices.chosen_trait_id == chosen_weakness_id
    )))

    db.commit()

async def practices_by_trait_type_get(db: Session, user_id: str, trait_type: str, dev_plan_id: str):
    chosen_trait_id = db.query(ChosenTraits.id).filter(
        ChosenTraits.user_id == user_id,
        ChosenTraits.development_plan_id == dev_plan_id,
        ChosenTraits.trait_type == trait_type,
    ).scalar()

    practices = db.query(Practices).filter(
        Practices.chosen_trait_id == chosen_trait_id
    ).all()

    return practices

async def practices_by_trait_type_get_2nd_sprint(db: Session, user_id: str, trait_type: str, dev_plan_id: str):
    chosen_trait_id = db.query(ChosenTraits.id).filter(
        ChosenTraits.user_id == user_id,
        ChosenTraits.development_plan_id == dev_plan_id,
        ChosenTraits.trait_type == trait_type,
    ).scalar()

    practices = db.query(Practices).filter(
        Practices.chosen_trait_id == chosen_trait_id
    ).all()

    # Check how many practices are already recommended
    recommended_practices = [practice for practice in practices if practice.is_recommended]
    
    if len(recommended_practices) >= 2:
        # If there are already two or more practices recommended, return practices as is
        return practices

    # Randomly select two practices
    recommended_practices = random.sample(practices, 2)

    for practice in recommended_practices:
        practice.is_recommended = True
        db.flush()
    db.commit()

    practices_updated = db.query(Practices).filter(
        Practices.chosen_trait_id == chosen_trait_id
    ).all()

    return practices_updated

def chosen_practices_save_one(db: Session, user_id: str, name: str, practice_id: str, chosen_trait_id: str, form_id: str, sprint_number: int, sprint_id: UUID, dev_plan_id: UUID):
    # check if user has existing chosen practices with same sprint id, dev plan id, and chosen trait id
    existing_chosen_practice = db.query(ChosenPractices).filter(
        ChosenPractices.user_id == user_id,
        ChosenPractices.chosen_trait_id == chosen_trait_id,
        ChosenPractices.sprint_id == sprint_id,
        ChosenPractices.development_plan_id == dev_plan_id
    ).first()

    if existing_chosen_practice:
        existing_chosen_practice.name = name
        existing_chosen_practice.practice_id = practice_id
        existing_chosen_practice.form_id = form_id
        
        chosen_practice_id = existing_chosen_practice.id
    else:
        chosen_practice = ChosenPractices(
            user_id=user_id,
            name=name,
            practice_id=practice_id,
            chosen_trait_id=chosen_trait_id,
            form_id=form_id,
            sprint_number=sprint_number,
            sprint_id=sprint_id,
            development_plan_id=dev_plan_id
        )
        db.add(chosen_practice)
        db.flush()
        chosen_practice_id = chosen_practice.id

    db.commit()

    return { "chosen_practice_id": chosen_practice_id }

async def chosen_practices_get(db: Session, user_id: str, sprint_number: int, dev_plan_id: str):
    chosen_strength_practice = db.query(ChosenPractices).join(
        ChosenTraits, ChosenPractices.chosen_trait_id == ChosenTraits.id
    ).filter(
        ChosenTraits.trait_type == "STRENGTH", 
        ChosenPractices.user_id == user_id,
        ChosenPractices.sprint_number == sprint_number,
        ChosenPractices.development_plan_id == dev_plan_id
    ).all()

    chosen_weakness_practice = db.query(ChosenPractices).join(
        ChosenTraits, ChosenPractices.chosen_trait_id == ChosenTraits.id
    ).filter(
        ChosenTraits.trait_type == "WEAKNESS", 
        ChosenPractices.user_id == user_id,
        ChosenPractices.sprint_number == sprint_number,
        ChosenPractices.development_plan_id == dev_plan_id
    ).all()

    return { "chosen_strength_practice": chosen_strength_practice, "chosen_weakness_practice": chosen_weakness_practice }


async def personal_practice_category_save_one(db: Session, user_id: str, name: str, dev_plan_id: str):
    # check if user already has an existing category with same dev plan id
    existing_category = db.query(PersonalPracticeCategory).filter(
        PersonalPracticeCategory.user_id == user_id,
        PersonalPracticeCategory.development_plan_id == dev_plan_id
    ).first()

    if existing_category:
        existing_category.name = name
        personal_practice_category_id = existing_category.id
    else:
        recommended_category = PersonalPracticeCategory(
            user_id=user_id,
            name=name,
            development_plan_id=dev_plan_id
        )
        
        db.add(recommended_category)
        db.flush()
        personal_practice_category_id = recommended_category.id

    db.commit()

    return{ "personal_practice_category_id": personal_practice_category_id }

async def personal_practice_category_get_one(db: Session, user_id: str, dev_plan_id: str):
    return db.query(PersonalPracticeCategory).filter(
        PersonalPracticeCategory.user_id == user_id,
        PersonalPracticeCategory.development_plan_id == dev_plan_id
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

async def personal_practice_category_and_chosen_personal_practices_clear_all(db: Session, user_id: str, dev_plan_id: str):
    personal_practice_category = db.query(PersonalPracticeCategory).filter(
        PersonalPracticeCategory.user_id == user_id,
        PersonalPracticeCategory.development_plan_id == dev_plan_id
    ).first()

    if personal_practice_category:
        db.execute(
        delete(ChosenPersonalPractices).where((
            ChosenPersonalPractices.personal_practice_category_id == personal_practice_category.id
        )))
        db.delete(personal_practice_category)

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
        ChosenPersonalPractices.user_id == user_id, 
        ChosenPersonalPractices.personal_practice_category_id == recommended_mind_body_category_id
    ).all()