
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.connection import get_db
from app.firebase.utils import verify_token
from app.utils.dev_plan_crud import dev_plan_create_get_one
from app.utils.forms_crud import forms_with_questions_options_get_all
from app.utils.answers_crud import answers_save_one, answers_get_all, answers_clear_all
from app.schemas.models import FormAnswerSchema

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/work-practices", tags=["work-practices"])

# Get Development Actions Form/Get Practice Guide Questions
@router.get("/get-actions-form")
async def get_development_actions_form(user_id: str, form_name: str, db: db_dependency, token = Depends(verify_token)):
  
  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )
  
  try:
    dev_plan = await dev_plan_create_get_one(user_id=user_id, db=db)
    return forms_with_questions_options_get_all(db, name=form_name, user_id=user_id, dev_plan_id=dev_plan["dev_plan_id"])
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
# Post Save Development Actions Answers(Direct user input, at most 3)
@router.post("/save-development-actions")
async def save_development_actions(answers: FormAnswerSchema, db: db_dependency, token = Depends(verify_token)):
  user_id = answers.user_id
  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )
  form_id = answers.form_id

  try:
    # Clear existing dev action answers - addresses case of going back and updating dev actions form
    await answers_clear_all(db=db, form_id=form_id)

    for answer in answers.answers:
      # Add all answers in DB 
      await answers_save_one(
        db=db,
        form_id=form_id,
        question_id=answer.question_id,
        option_id=answer.option_id,
        answer=answer.answer
      )

    return { "message": "Development Actions Saved" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Written Development Actions
@router.get("/development-actions")
async def get_development_actions(user_id: str, trait_type: str, sprint_number: int, db: db_dependency, token = Depends(verify_token)):
  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )
  # Fetch from the Answers DB table under the form of strength/weakness practice
  form_name = f"{sprint_number}_{trait_type}_PRACTICE_QUESTIONS"

  try:
    dev_plan = await dev_plan_create_get_one(user_id=user_id, db=db) 
    return await answers_get_all(db=db, user_id=user_id, form_name=form_name, sprint_number=sprint_number, dev_plan_id=dev_plan["dev_plan_id"])
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# not in current estimates -- not sure if the user can update it in the next loop of the dev plan
@router.post("/update-development-actions/{user_id}")
async def update_development_actions():
  try:
    return { "message": "Development Actions Updated" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))