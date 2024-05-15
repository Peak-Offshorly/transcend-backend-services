from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from app.schemas.models import DataFormSchema
from app.database.connection import get_db
from app.utils.dates_crud import add_dates, compute_second_sprint_dates, compute_colleague_message_dates
from app.utils.sprints_crud import get_sprint_start_end_date, get_sprint_start_end_date_sprint_number
from app.utils.traits_crud import chosen_traits_get
from app.utils.answers_crud import answers_get_all
from app.utils.practices_crud import chosen_personal_practices_get_all, personal_practice_category_get_one, chosen_practices_get

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/development-plan", tags=["development-plan"])

# Adds dates for Gantt chart shown in Sprint 1; this endpoint should ONLY called in sprint 1
@router.post("/add-dates")
async def create_gantt_chart_dates(data: DataFormSchema, db: db_dependency):
  user_id = data.user_id
  try:
    chosen_traits_data = chosen_traits_get(db=db, user_id=user_id)
    recommended_mind_body_category_data = await personal_practice_category_get_one(db=db, user_id=user_id)
    chosen_trait_practices = await chosen_practices_get(db=db, user_id=user_id, sprint_number=1)

    # Create Dev Plan

    await add_dates(
      db=db,
      chosen_traits_data=chosen_traits_data,
      recommended_mind_body_category_data=recommended_mind_body_category_data,
      chosen_trait_practices=chosen_trait_practices
    )
    
    return { "message": "Start and end dates added." }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Development Plan Gantt Chart
@router.get("/gantt-chart-data")
async def get_gantt_chart(user_id: str, db: db_dependency):
  try:
    chosen_traits = chosen_traits_get(db=db, user_id=user_id)
    chosen_trait_practices_1 = await chosen_practices_get(db=db, user_id=user_id, sprint_number=1) # Chosen Practices for Sprint 1 
    recommended_mind_body_category = await personal_practice_category_get_one(db=db, user_id=user_id)
    sprint_1_dates = await get_sprint_start_end_date(db=db, user_id=user_id, sprint_id=chosen_trait_practices_1["chosen_strength_practice"][0].sprint_id)

    # Get or Compute Sprint 2 start/end date
    existing_sprint_2_dates = await get_sprint_start_end_date_sprint_number(db=db, user_id=user_id, sprint_number=2)
    if existing_sprint_2_dates:
      sprint_2_dates = existing_sprint_2_dates
      chosen_trait_practices_2 = await chosen_practices_get(db=db, user_id=user_id, sprint_number=2)
    else:
      sprint_2_dates = await compute_second_sprint_dates(start_to_mid_date=sprint_1_dates["end_date"], end_date=chosen_traits["chosen_strength"]["end_date"])
      chosen_trait_practices_2 = None

    # Compute dates for Colleague messages
    colleague_message_dates = await compute_colleague_message_dates(start_date=recommended_mind_body_category.start_date, end_date=recommended_mind_body_category.end_date)
    
    return {
      "colleague_message_1": {
        "start_date": colleague_message_dates["week_1"][0],
        "end_date": colleague_message_dates["week_1"][1]
      },
      "colleague_message_2": {
        "start_date": colleague_message_dates["week_5"][0],
        "end_date": colleague_message_dates["week_5"][1]
      },
      "colleague_message_3": {
        "start_date": colleague_message_dates["week_9"][0],
        "end_date": colleague_message_dates["week_9"][1]
      },
      "colleague_message_4": {
        "start_date": colleague_message_dates["week_12"][0],
        "end_date": colleague_message_dates["week_12"][1]
      },
      "chosen_strength": chosen_traits["chosen_strength"],
      "chosen_weakness": chosen_traits["chosen_weakness"],
      "sprint_1": {
        "start_date" : sprint_1_dates["start_date"],
        "end_date" : sprint_1_dates["end_date"],
        "strength_practice": chosen_trait_practices_1["chosen_strength_practice"][0].name,
        "weakness_practice": chosen_trait_practices_1["chosen_weakness_practice"][0].name,
      },
      "sprint_2": {
        "start_date" : sprint_2_dates["start_date"],
        "end_date" : sprint_2_dates["end_date"],
        "strength_practice": chosen_trait_practices_2["chosen_strength_practice"][0].name if chosen_trait_practices_2 else None,
        "weakness_practice": chosen_trait_practices_2["chosen_weakness_practice"][0].name if chosen_trait_practices_2 else None
      },
      "mind_body_practice": {
        "name": recommended_mind_body_category.name,
        "start_date": recommended_mind_body_category.start_date,
        "end_date": recommended_mind_body_category.end_date
      }
    }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Details of Plan -- for Review Page
@router.get("/review-details")
async def get_review_details(user_id: str, sprint_number: int, db: db_dependency):
  try:
    # Strength/Weakness
    chosen_traits = chosen_traits_get(db=db, user_id=user_id)

    # Practice for Strength/Weakness
    chosen_trait_practices = await chosen_practices_get(db=db, user_id=user_id, sprint_number=sprint_number)
    
    # Dev actions for each strength/weakness practice
    strength_form_name = f"{sprint_number}_STRENGTH_PRACTICE_QUESTIONS"
    weakness_form_name = f"{sprint_number}_WEAKNESS_PRACTICE_QUESTIONS"
    strength_practice_dev_actions= await answers_get_all(db=db, user_id=user_id, form_name=strength_form_name, sprint_number=sprint_number)
    weakness_practice_dev_actions= await answers_get_all(db=db, user_id=user_id, form_name=weakness_form_name, sprint_number=sprint_number)

    # Mind Body Practice category and Chosen Recommendations
    recommended_mind_body_category = await personal_practice_category_get_one(db=db, user_id=user_id)
    chosen_recommendations = await chosen_personal_practices_get_all(db=db, user_id=user_id, recommended_mind_body_category_id=recommended_mind_body_category.id)
    
    return { 
      "chosen_strength": chosen_traits["chosen_strength"],
      "strength_practice": chosen_trait_practices["chosen_strength_practice"],
      "strength_practice_dev_actions": strength_practice_dev_actions,
      "chosen_weakness": chosen_traits["chosen_weakness"],
      "weakness_practice": chosen_trait_practices["chosen_weakness_practice"],
      "weakness_practice_dev_actions": weakness_practice_dev_actions,
      "mind_body_practice": recommended_mind_body_category,
      "mind_body_chosen_recommendations": chosen_recommendations
    }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))