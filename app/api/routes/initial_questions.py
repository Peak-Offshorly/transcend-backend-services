from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.connection import get_db
from app.schemas.models import DataFormSchema, FormSchema, QuestionSchema, OptionSchema
from app.utils.traits_crud import traits_create
from app.utils.forms_crud import (
    forms_with_questions_options_get_all, 
    forms_with_initial_questions_options_answers_get_all, 
    forms_create_one_initial_questions_form, 
    form_initial_questions_with_options_get_all
)

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/initial-questions", tags=["initial-questions"])

# Get Initial Questions - slightly different Get since we get the individual questions and options and don't connect it to a specific Form id
# Returns: Form Schema (Form, Questions, Options, Answers)
@router.get("/get-form")
async def create_get_traits_and_form_questions_options(data: DataFormSchema, db: db_dependency):
  try:
    form_name = data.form_name
    user_id = data.user_id
    
    form_exists = forms_with_questions_options_get_all(db=db, name=form_name, user_id=user_id)
    
    # return form schema with form_id if Form exists already
    if form_exists:
      return form_initial_questions_with_options_get_all(db=db, form_name=form_name, user_id=user_id, form_id=form_exists.id)
    
    # No initial qs form yet, create traits and new initial questions Form for user
    # Create new Traits for user
    traits_create(db=db, user_id=user_id)
    
    # Create Form in db
    form_data_schema = FormSchema(
      name=form_name,
      user_id=user_id
    )
    new_form = forms_create_one_initial_questions_form(db=db, form=form_data_schema)

    return new_form
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

@router.get("/get-form-answers")
async def get_answers(data: DataFormSchema, db: db_dependency):
  try:
    name = data.form_name
    user_id = data.user_id

    form = forms_with_initial_questions_options_answers_get_all(db, name=name, user_id=user_id)

    return form
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Post Save Initial Answers; would have calculations based on chosen answers
@router.post("/save-answers/{user_id}")
async def save_initial_questions_answers(user_id, db: db_dependency):
  try:
    return None
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

@router.get("/all")
async def get_all_initial_questions(db: db_dependency):
  try:
    # return initial_questions_get_all(db)
    return {"message": "get all"}
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

@router.get("/{initial_question_id}")
async def get_one_initial_question(initial_question_id, db: db_dependency):
  try:
    # return initial_questions_get_one(db=db, id=id)
    return {"message": "get one"}
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
