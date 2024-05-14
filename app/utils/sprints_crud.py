from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database.models import Sprints

async def sprint_create_get_one(db: Session, user_id: str):
    # get max sprint number of user
    max_sprint = db.query(func.max(Sprints.number)).filter(
        Sprints.user_id == user_id
    ).scalar()
    
    # no sprint yet, first sprint
    if max_sprint is None:
        first_sprint = Sprints(
            user_id=user_id,
            number=1
        )
        db.add(first_sprint)
        db.flush()
        db.commit()
        
        return { "sprint_number": first_sprint.number, "sprint_id": first_sprint.id }

    # check if user has max Sprint that is finished
    has_finished_sprint = db.query(Sprints).filter(
        Sprints.user_id == user_id,
        Sprints.number == max_sprint,
        Sprints.is_finished == True
    ).first()

    if has_finished_sprint:
        next_sprint = Sprints(
            user_id=user_id,
            number=has_finished_sprint.number + 1 # iterate by one to signify next sprint
        )
        db.add(next_sprint)
        db.flush()
        db.commit()

        sprint_number = next_sprint.number
        sprint_id = next_sprint.id
    else:
        # get existing max sprint that is not finished
        existing_sprint = db.query(Sprints).filter(
            Sprints.user_id == user_id,
            Sprints.number == max_sprint
        ).first()
        
        sprint_number = existing_sprint.number
        sprint_id = existing_sprint.id
    
    
    return { "sprint_number": sprint_number, "sprint_id": sprint_id }

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
async def get_sprint_start_end_date_sprint_number(db: Session, user_id: str, sprint_number: int):
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