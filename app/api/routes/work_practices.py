
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.connection import get_db
from app.utils.forms_crud import forms_with_questions_options_get_all
from app.utils.answers_crud import answers_save_one
from app.schemas.models import FormAnswerSchema

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/work-practices", tags=["work-practices"])

@router.get("/questions/{user_id}")
async def get_questions():
  try:
    forms_with_questions_options_get_all()

    return { "message": "Guide Qeuestions" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Development Actions Form/Get Practice Guide Questions
@router.get("/get-actions-form")
async def get_development_actions_form(user_id: str, form_name: str, db: db_dependency):
  try:
    return forms_with_questions_options_get_all(db, name=form_name, user_id=user_id)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
# Post Save Development Actions Answers(Direct user input, at most 3)
@router.post("/save-development-actions")
async def save_development_actions(answers: FormAnswerSchema, db: db_dependency):
  form_id = answers.form_id

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

    return { "message": "Development Actions Saved" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Written Development Actions
@router.get("/development-actions")
async def get_development_actions(user_id: str, trait_type: str, sprint_number: int, db: db_dependency):
  # Basically it's gonna fetch from the Answers under the form of strength/weakness practice
  try:
    return { "message": "Development Actions Created" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# not in current estimates -- not sure if the user can update it in the next loop of the dev plan
@router.post("/update-development-actions/{user_id}")
async def update_development_actions():
  try:
    return { "message": "Development Actions Updated" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))