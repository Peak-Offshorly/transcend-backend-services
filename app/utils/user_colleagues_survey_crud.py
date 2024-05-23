from typing import Optional
from sqlalchemy.orm import Session
from app.database.models import UserColleaguesSurvey, UserColleagues

async def survey_save_one(db: Session, user_colleague_id: str, q1_answer: int, q2_answer: int, q3_answer: int, q4_answer: Optional[str] = None, q5_answer: Optional[str] = None):
    existing_colleague = db.query(UserColleagues).filter(
        UserColleagues.id == user_colleague_id
    ).first()

    if existing_colleague.survey_completed:
        return { "message": "Colleague id already has a survey entry" }

    new_survey_entry = UserColleaguesSurvey(
        user_colleague_id=user_colleague_id,
        effective_leader=q1_answer,
        effective_strength_area=q2_answer,
        effective_weakness_area=q3_answer,
        particularly_effective=q4_answer,
        more_effective=q5_answer
    ) 
    db.add(new_survey_entry)
    db.flush()

    # Set survey completed of colleague to True
    existing_colleague.survey_completed = True
    db.commit()

    return { "message": "Colleague survey entry saved" }

async def survey_get_all(db: Session, user_id: str, dev_plan_id: str):
    all_user_colleagues = db.query(UserColleagues).filter(
        UserColleagues.user_id == user_id,
        UserColleagues.development_plan_id == dev_plan_id
    ).all()

    # Extract colleague_ids
    colleague_ids = [colleague.id for colleague in all_user_colleagues]

    # Get all UserColleaguesSurvey for the colleague_ids
    user_colleagues_surveys = db.query(UserColleaguesSurvey).filter(
        UserColleaguesSurvey.user_colleague_id.in_(colleague_ids)
    ).all()

    return user_colleagues_surveys