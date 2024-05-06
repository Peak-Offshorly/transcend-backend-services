
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.connection import get_db
from app.utils.forms_crud import forms_with_questions_options_get_all, forms_create_one, forms_with_questions_options_answers_get_all
from app.schemas.models import DataFormSchema, FormSchema, QuestionSchema, OptionSchema

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/work-practices", tags=["work-practices"])

# Get Practice Guide Questions
@router.get("/questions/{user_id}")
async def get_questions():
  try:
    forms_with_questions_options_get_all()

    return { "message": "Guide Qeuestions" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Development Actions Form
@router.get("/get-actions-form")
async def get_development_actions_form(user_id: str, form_name: str, db: db_dependency):
  try:
    return forms_with_questions_options_get_all(db, name=form_name, user_id=user_id)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
# Post Save Development Actions (Direct user input, at most 3)
@router.post("/save-development-actions/{user_id}")
async def save_development_actions():
  try:
    return { "message": "Development Actions Saved" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Written Development Actions
@router.get("/development-actions/{user_id}")
async def get_development_actions():
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