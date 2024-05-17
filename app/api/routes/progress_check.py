import pytz
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Annotated
from app.schemas.models import DataFormSchema, FormAnswerSchema
from app.database.connection import get_db
from app.utils.sprints_crud import sprint_create_get_one
from app.utils.answers_crud import answers_get_all, answers_save_one
from app.utils.forms_crud import form_questions_options_get_all, forms_with_questions_options_sprint_id_get_all, forms_create_one

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/progress-check", tags=["progress-check"])

# Get Written Development Actions as Questions - Strength
# Progress check is done per week for each 6 week sprint
@router.post("/questions-strength-practice")
async def get_development_progress_questions_strength_practice(db: db_dependency, data: DataFormSchema):
  user_id = data.user_id
  # Determine which sprint you are in
  sprint = await sprint_create_get_one(db=db, user_id=user_id)
  sprint_number = sprint["sprint_number"]
  sprint_id = sprint["sprint_id"]

  # Calculate current week number
  start_date =  sprint["start_date"]
  current_date = datetime.now(pytz.utc)
  delta = current_date - start_date
  week_number = (delta.days // 7) + 1  # Adding 1 to make week_number start from 1
  if week_number > 6:
      week_number = 6  # Assuming the range is up to 6 weeks
  
  # <SPRINT_NUM>_PROGRESS_STRENGTH_WEEK_<WEEK NUMBER>
  form_name = f"{sprint_number}_PROGRESS_STRENGTH_WEEK_{week_number}"
  questions=[]
  options=[
    "Complete",
    "Mostly Completed",
    "Partially Completed",
    "Thought about it",
    "Did not do"
  ]
  ranks=[] 
  try:
    # Return if Form exists
    form_exists = forms_with_questions_options_sprint_id_get_all(db=db, name=form_name, user_id=user_id, sprint_id=sprint_id)
    if form_exists:
      return form_exists
    else:
      # Fetch from the Answers DB table under the form of strength/weakness practice
      dev_actions_form_name = f"{sprint_number}_STRENGTH_PRACTICE_QUESTIONS"
      dev_actions = await answers_get_all(db=db, user_id=user_id, form_name=dev_actions_form_name, sprint_number=sprint_number)

      for action in dev_actions:
        questions.append(action.answer)
        ranks.append(0)

      form_data = form_questions_options_get_all(
        user_id=user_id,
        form_name=form_name,
        option_type="likert_scale",
        category="PROGRESS_CHECK_STRENGTH_DEV_ACTIONS_QS",
        questions=questions,
        options=options,
        ranks=ranks,
        sprint_id=sprint_id,
        sprint_number=sprint_number
      )
      await forms_create_one(db=db, form=form_data)

      return forms_with_questions_options_sprint_id_get_all(db=db, name=form_name, user_id=user_id, sprint_id=sprint_id)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Written Development Actions as Questions - Weakness
# Progress check is done per week for each 6 week sprint
@router.post("/questions-weakness-practice")
async def get_development_progress_questions_weakness_practice(db: db_dependency, data: DataFormSchema):
  user_id = data.user_id
  # Determine which sprint you are in
  sprint = await sprint_create_get_one(db=db, user_id=user_id)
  sprint_number = sprint["sprint_number"]
  sprint_id = sprint["sprint_id"]

  # Calculate current week number
  start_date =  sprint["start_date"]
  current_date = datetime.now(pytz.utc)
  delta = current_date - start_date
  week_number = (delta.days // 7) + 1  # Adding 1 to make week_number start from 1
  if week_number > 6:
      week_number = 6  # Assuming the range is up to 6 weeks
  
  # <SPRINT_NUM>_PROGRESS_WEAKNESS_WEEK_<WEEK NUMBER>
  form_name = f"{sprint_number}_PROGRESS_WEAKNESS_WEEK_{week_number}"
  questions=[]
  options=[
    "Complete",
    "Mostly Completed",
    "Partially Completed",
    "Thought about it",
    "Did not do"
  ]
  ranks=[] 
  try:
    # Return if Form exists
    form_exists = forms_with_questions_options_sprint_id_get_all(db=db, name=form_name, user_id=user_id, sprint_id=sprint_id)
    if form_exists:
      return form_exists
    else:
      # Fetch from the Answers DB table under the form of strength/weakness practice
      dev_actions_form_name = f"{sprint_number}_WEAKNESS_PRACTICE_QUESTIONS"
      dev_actions = await answers_get_all(db=db, user_id=user_id, form_name=dev_actions_form_name, sprint_number=sprint_number)

      for action in dev_actions:
        questions.append(action.answer)
        ranks.append(0)

      form_data = form_questions_options_get_all(
        user_id=user_id,
        form_name=form_name,
        option_type="likert_scale",
        category="PROGRESS_CHECK_WEAKNESS_DEV_ACTIONS_QS",
        questions=questions,
        options=options,
        ranks=ranks,
        sprint_id=sprint_id,
        sprint_number=sprint_number
      )
      await forms_create_one(db=db, form=form_data)

      return forms_with_questions_options_sprint_id_get_all(db=db, name=form_name, user_id=user_id, sprint_id=sprint_id)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Post Save Answers for Written Development Actions as Questions - can be used for both Strength and Weakness
@router.post("/save-answers")
async def save_development_progress_answers(db: db_dependency, answers: FormAnswerSchema):
  form_id = answers.form_id
  form_name = answers.form_name
  form_name_parts = form_name.split("_")

  try:
    for answer in answers.answers:
      # Add all answers in DB 
      await answers_save_one(
        db=db,
        form_id=form_id,
        question_id=answer.question_id,
        option_id=answer.option_id,
        answer=answer.answer
      )

    return { "message": f"{form_name_parts[2].capitalize()} Development Actions Progress Check for Week {form_name_parts[-1]} Saved." }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get answers for Progress Check - might be used for weekly email nudge to user
@router.get("/get-answers")
async def save_development_progress_answers(db: db_dependency, trait_type: str, sprint_number: int, week_number: int, user_id: str):
  try:
    if week_number > 6:
      return { "message": "Week number too big." }
  
    # <SPRINT_NUM>_PROGRESS_WEAKNESS_WEEK_<WEEK NUMBER>
    form_name = f"{sprint_number}_PROGRESS_{trait_type.upper()}_WEEK_{week_number}"

    return await answers_get_all(db=db, user_id=user_id, form_name=form_name, sprint_number=sprint_number)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
