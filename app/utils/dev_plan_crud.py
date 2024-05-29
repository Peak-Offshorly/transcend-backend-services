from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database.models import DevelopmentPlan

async def dev_plan_create_get_one(user_id: str, db: Session):
    max_dev_plan_number = db.query(func.max(DevelopmentPlan.number)).filter(
        DevelopmentPlan.user_id == user_id
    ).scalar()

    if max_dev_plan_number is None:
        first_dev_plan = DevelopmentPlan(
            user_id=user_id,
            number=1
        )
        db.add(first_dev_plan)
        db.flush()
        db.commit()
        
        return { 
            "dev_plan_number": first_dev_plan.number, 
            "dev_plan_id": first_dev_plan.id,
            "start_date": first_dev_plan.start_date,
            "end_date": first_dev_plan.end_date
        }
    
    has_finished_dev_plan = db.query(DevelopmentPlan).filter(
        DevelopmentPlan.user_id == user_id,
        DevelopmentPlan.number == max_dev_plan_number,
        DevelopmentPlan.is_finished == True
    ).first()

    if has_finished_dev_plan:
        next_dev_plan = DevelopmentPlan(
            user_id=user_id,
            number=has_finished_dev_plan.number + 1 # iterate by one
        )
        db.add(next_dev_plan)
        db.flush()
        db.commit()

        dev_plan_number = next_dev_plan.number
        dev_plan_id = next_dev_plan.id
        start_date = next_dev_plan.start_date
        end_date = next_dev_plan.end_date
    else:
        # get existing dev plan that is not finished
        existing_dev_plan = db.query(DevelopmentPlan).filter(
            DevelopmentPlan.user_id == user_id,
            DevelopmentPlan.number == max_dev_plan_number
        ).first()
        
        dev_plan_number = existing_dev_plan.number
        dev_plan_id = existing_dev_plan.id
        start_date = existing_dev_plan.start_date
        end_date = existing_dev_plan.end_date
    
    return { 
        "dev_plan_number": dev_plan_number, 
        "dev_plan_id": dev_plan_id,
        "start_date": start_date,
        "end_date": end_date
    }

async def dev_plan_get_current(db: Session, user_id: str):
    # get max dev plan number of user
    max_dev_plan = db.query(func.max(DevelopmentPlan.number)).filter(
        DevelopmentPlan.user_id == user_id
    ).scalar()

    if max_dev_plan is None:
        return{
            "message": "User has no development plan yet."
        }

    existing_dev_plan = db.query(DevelopmentPlan).filter(
        DevelopmentPlan.user_id == user_id,
        DevelopmentPlan.number == max_dev_plan,
        DevelopmentPlan.is_finished == False
    ).first()

    return { 
        "dev_plan_id": existing_dev_plan.id,
        "dev_plan_number": existing_dev_plan.number,
        "start_date": existing_dev_plan.start_date,
        "end_date": existing_dev_plan.end_date
    }

async def dev_plan_update_chosen_traits(user_id: str, chosen_strength_id: str, chosen_weakness_id: str, db: Session):
    dev_plan = await dev_plan_get_current(user_id=user_id, db=db)

    existing_dev_plan = db.query(DevelopmentPlan).filter(
        DevelopmentPlan.id == dev_plan["dev_plan_id"]
    ).first()
    
    existing_dev_plan.chosen_strength_id = chosen_strength_id
    existing_dev_plan.chosen_weakness_id = chosen_weakness_id
    
    db.commit()

async def dev_plan_update_sprint(user_id: str, sprint_number: int, sprint_id: str, db: Session):
    dev_plan = await dev_plan_get_current(user_id=user_id, db=db)

    existing_dev_plan = db.query(DevelopmentPlan).filter(
        DevelopmentPlan.id == dev_plan["dev_plan_id"]
    ).first()

    if sprint_number == 1:
        existing_dev_plan.sprint_1_id = sprint_id
    else:
        existing_dev_plan.sprint_2_id = sprint_id
    
    db.commit()

async def dev_plan_update_chosen_strength_practice(user_id: str, sprint_number: int, chosen_strength_id: str, db: Session):
    dev_plan = await dev_plan_get_current(user_id=user_id, db=db)

    existing_dev_plan = db.query(DevelopmentPlan).filter(
        DevelopmentPlan.id == dev_plan["dev_plan_id"]
    ).first()

    if sprint_number == 1:
        existing_dev_plan.chosen_strength_practice_1_id = chosen_strength_id
    else:
        existing_dev_plan.chosen_strength_practice_2_id = chosen_strength_id
    
    db.commit()

async def dev_plan_update_chosen_weakness_practice(user_id: str, sprint_number: int, chosen_weakness_id: str, db: Session):
    dev_plan = await dev_plan_get_current(user_id=user_id, db=db)

    existing_dev_plan = db.query(DevelopmentPlan).filter(
        DevelopmentPlan.id == dev_plan["dev_plan_id"]
    ).first()

    if sprint_number == 1:
        existing_dev_plan.chosen_weakness_practice_1_id = chosen_weakness_id
    else:
        existing_dev_plan.chosen_weakness_practice_2_id = chosen_weakness_id
    
    db.commit()

async def dev_plan_update_personal_practice_category(user_id: str, personal_practice_category_id: str, db: Session):
    dev_plan = await dev_plan_get_current(user_id=user_id, db=db)

    existing_dev_plan = db.query(DevelopmentPlan).filter(
        DevelopmentPlan.id == dev_plan["dev_plan_id"]
    ).first()

    existing_dev_plan.personal_practice_category_id = personal_practice_category_id
    
    db.commit()

async def dev_plan_update_is_finished_true(db: Session, user_id: str, dev_plan_id: str):
    existing_dev_plan = db.query(DevelopmentPlan).filter(
        DevelopmentPlan.id == dev_plan_id,
        DevelopmentPlan.user_id == user_id,
        DevelopmentPlan.is_finished == False
    ).first()

    if existing_dev_plan:
        # Check if all required fields have valid entries
        required_fields = [
            existing_dev_plan.chosen_strength_id,
            existing_dev_plan.chosen_weakness_id,
            existing_dev_plan.sprint_1_id,
            existing_dev_plan.chosen_strength_practice_1_id,
            existing_dev_plan.chosen_weakness_practice_1_id,
            existing_dev_plan.sprint_2_id,
            existing_dev_plan.chosen_strength_practice_2_id,
            existing_dev_plan.chosen_weakness_practice_2_id,
            existing_dev_plan.personal_practice_category_id
        ]
        
        if all(field is not None for field in required_fields):
            existing_dev_plan.is_finished = True
            db.flush()
            db.commit()
            return { "message": f"Development Plan ID {existing_dev_plan.id} is finished" }
        else:
            return { "message": f"Development Plan not yet complete" }
    
    return { "message": "Development Plan does not exist" }