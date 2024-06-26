from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Annotated
from app.schemas.models import DataFormSchema, FormSchema, FormAnswerSchema
from app.database.connection import get_db
from app.firebase.utils import verify_token
from app.utils.dev_plan_crud import dev_plan_create_get_one
from app.utils.traits_crud import traits_create, traits_compute_tscore
from app.utils.answers_crud import answers_to_initial_questions_save
from app.utils.update_traits import check_user_count_divisible_by_ten, update_ave_std, increment_count
from app.utils.forms_crud import (
    forms_with_questions_options_get_all,
    forms_create_one_initial_questions_form, 
    form_initial_questions_with_options_get_all,
    initial_questions_forms_with_questions_options_get_all
)

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/initial-questions", tags=["initial-questions"])

# Get Initial Questions - slightly different Get since we get the individual questions and options and don't connect it to a specific Form id
# Returns: Form Schema (Form, Questions, Options, Answers)
@router.post("/get-form")
async def create_get_traits_and_form_questions_options(data: DataFormSchema, db: db_dependency, token = Depends(verify_token)):
  form_name = data.form_name
  user_id = data.user_id

  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )

  try:
    form_exists = initial_questions_forms_with_questions_options_get_all(db=db, name=form_name, user_id=user_id)
    
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
async def save_initial_questions_answers(answers: FormAnswerSchema, db: db_dependency, background_tasks: BackgroundTasks, token = Depends(verify_token)):
  user_id = answers.user_id

  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )
  
  try:
    await answers_to_initial_questions_save(db=db, answers=answers)
    traits_compute_tscore(db=db, answers=answers)

    # Schedule the update operation as a background task if 10 additional inputs
    if increment_count(db=db, user_id=user_id):
      background_tasks.add_task(update_ave_std, db)
      
    return { "message": "Initial question answers saved and t-scores computed." }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
