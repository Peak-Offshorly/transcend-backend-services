from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.connection import get_db
from app.schemas.models import DataFormSchema, FormSchema, InitialAnswerSchema
from app.utils.traits_crud import traits_create, traits_compute_tscore
from app.utils.answers_crud import answers_to_initial_questions_save
from app.utils.forms_crud import (
    forms_with_questions_options_get_all,
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

# Post Save Initial Answers: would have calculations based on chosen answers
# Returns: Success Message
@router.post("/save-answers")
async def save_initial_questions_answers(request: Request, db: db_dependency):
  payload = await request.json()
  answers = InitialAnswerSchema.model_validate(payload)
  try:
    await answers_to_initial_questions_save(db=db, answers=answers)
    traits_compute_tscore(db=db, answers=answers)

    return { "message": "Initial question answers saved and t-scores computed." }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
