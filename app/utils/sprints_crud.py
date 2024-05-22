from datetime import datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database.models import Sprints

async def sprint_create_get_one(db: Session, user_id: str, dev_plan_id: str):
    # get max sprint number of user for that dev plan id
    max_sprint = db.query(func.max(Sprints.number)).filter(
        Sprints.user_id == user_id,
        Sprints.development_plan_id == dev_plan_id
    ).scalar()
    
    # no sprint yet under that dev plan id, first sprint for that dev plan
    if max_sprint is None:
        first_sprint = Sprints(
            user_id=user_id,
            number=1,
            development_plan_id=dev_plan_id
        )
        db.add(first_sprint)
        db.flush()
        db.commit()
        
        return { 
            "sprint_number": first_sprint.number, 
            "sprint_id": first_sprint.id,
            "start_date": first_sprint.start_date,
            "end_date": first_sprint.end_date
        }

    # user has max Sprint, check if it is finished
    has_finished_sprint = db.query(Sprints).filter(
        Sprints.user_id == user_id,
        Sprints.development_plan_id == dev_plan_id,
        Sprints.number == max_sprint,
        Sprints.is_finished == True
    ).first()

    if has_finished_sprint:
        if max_sprint < 2: # sprint 1 is finished
            next_sprint = Sprints(
                user_id=user_id,
                development_plan_id=dev_plan_id,
                number=2 # sprint number 2 now, since it is safe to assume the finished sprint is sprint 1
            )
            db.add(next_sprint)
            db.flush()
            db.commit()

            sprint_number = next_sprint.number
            sprint_id = next_sprint.id
            start_date = next_sprint.start_date
            end_date = next_sprint.end_date
    else:
        # get existing max sprint that is not finished
        existing_sprint = db.query(Sprints).filter(
            Sprints.user_id == user_id,
            Sprints.number == max_sprint
        ).first()
        
        sprint_number = existing_sprint.number
        sprint_id = existing_sprint.id
        start_date = existing_sprint.start_date
        end_date = existing_sprint.end_date
    
    return { 
        "sprint_number": sprint_number, 
        "sprint_id": sprint_id,
        "start_date": start_date,
        "end_date": end_date
    }

async def sprint_get_current(db: Session, user_id: str, dev_plan_id: str):
    # get max sprint number of user with certain dev plan id
    max_sprint = db.query(func.max(Sprints.number)).filter(
        Sprints.user_id == user_id,
        Sprints.development_plan_id == dev_plan_id
    ).scalar()

    # no sprint yet, first sprint
    if max_sprint is None:
        return{
            "sprint_number": 1,
            "sprint_id": None
        }

    existing_sprint = db.query(Sprints).filter(
        Sprints.user_id == user_id,
        Sprints.development_plan_id == dev_plan_id,
        Sprints.number == max_sprint
    ).first()

    return { 
        "sprint_number": existing_sprint.number, 
        "sprint_id": existing_sprint.id
    }

async def sprint_update_is_finished_true(db: Session, user_id: str, sprint_id: str, dev_plan_id: str):
    existing_sprint = db.query(Sprints).filter(
        Sprints.id == sprint_id,
        Sprints.user_id == user_id,
        Sprints.development_plan_id == dev_plan_id,
        Sprints.is_finished == False
    ).first()

    if existing_sprint:
        if existing_sprint.number > 2:
            return { 
                "message": "2 sprints max"
            } 
        existing_sprint.is_finished = True
        db.flush()
    
    db.commit()
    return { "message": f"Sprint {existing_sprint.number} with id {existing_sprint.id} is finished!" }

async def sprint_update_second_sprint_dates(db: Session, user_id: str, sprint_id: str, dev_plan_id: str, start_date: datetime, end_date: datetime):
    # We assume this is sprint 2
    existing_sprint_2 = db.query(Sprints).filter(
        Sprints.id == sprint_id,
        Sprints.user_id == user_id,
        Sprints.development_plan_id == dev_plan_id,
    ).first()

    existing_sprint_2.start_date = start_date
    existing_sprint_2.end_date = end_date

    db.commit()

async def sprint_update_strength_form_id(db: Session, user_id: str, sprint_id: str, strength_form_id: str):
    existing_sprint =  db.query(Sprints).filter(
        Sprints.user_id == user_id,
        Sprints.id == sprint_id,
    ).first()

    if existing_sprint:
        existing_sprint.strength_practice_form_id = strength_form_id

    db.commit()

async def sprint_update_weakness_form_id(db: Session, user_id: str, sprint_id: str, weakness_form_id: str):
    existing_sprint =  db.query(Sprints).filter(
        Sprints.user_id == user_id,
        Sprints.id == sprint_id,
    ).first()

    if existing_sprint:
        existing_sprint.weakness_practice_form_id = weakness_form_id

    db.commit()

# Get based on sprint_id
async def get_sprint_start_end_date(db: Session, user_id: str, sprint_id: str):
    existing_sprint =  db.query(Sprints).filter(
        Sprints.user_id == user_id,
        Sprints.id == sprint_id,
    ).first()

    return {
        "sprint_id": sprint_id, 
        "sprint_number": existing_sprint.number, 
        "start_date": existing_sprint.start_date,
        "end_date": existing_sprint.end_date
    }

# Get based on sprint_number
async def get_sprint_start_end_date_sprint_number(db: Session, user_id: str, sprint_number: int, dev_plan_id: str):
    existing_sprint =  db.query(Sprints).filter(
        Sprints.user_id == user_id,
        Sprints.number == sprint_number,
    ).first()

    if existing_sprint is None:
        return None

    return {
        "sprint_id": existing_sprint.id, 
        "sprint_number": existing_sprint.number, 
        "start_date": existing_sprint.start_date,
        "end_date": existing_sprint.end_date
    }