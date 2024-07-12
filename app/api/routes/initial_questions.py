from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Annotated, List
from app.schemas.models import DataFormSchema, FormSchema, FormAnswerSchema, AnswerSchema
from app.database.connection import get_db
from app.firebase.utils import verify_token
from app.utils.dev_plan_crud import dev_plan_get_current, dev_plan_clear_fields
from app.utils.traits_crud import traits_create, traits_compute_tscore, chosen_traits_clear, chosen_traits_get
from app.utils.answers_crud import answers_to_initial_questions_save, are_matching_answers
from app.utils.update_traits import update_ave_std, increment_count
from app.utils.practices_crud import practices_and_chosen_practices_clear_all, personal_practice_category_and_chosen_personal_practices_clear_all
from app.utils.pending_actions_crud import pending_actions_clear_all
from app.utils.sprints_crud import sprint_get_current, sprint_clear_fields
from app.utils.forms_crud import (
    forms_create_one_initial_questions_form, 
    form_initial_questions_with_options_get_all,
    initial_questions_forms_with_questions_options_get_all,
    delete_form_and_associations_form_name
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
    # Check if answers match existing answers
    answers_match = await are_matching_answers(db=db, user_id=user_id, form_name="1_INITIAL_QUESTIONS", sprint_number=None, dev_plan_id=None, new_answers=answers.answers)

    if answers_match:
      pass
    else:
      await answers_to_initial_questions_save(db=db, answers=answers)
      traits_compute_tscore(db=db, answers=answers)

      if answers_match == False:
        # ----Clear succeeding forms/practices/traits
        dev_plan = await dev_plan_get_current(db=db, user_id=user_id)
        if dev_plan:
          dev_plan_id = dev_plan["dev_plan_id"]
          chosen_traits = chosen_traits_get(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
          if chosen_traits:
            # Clear dev plan fields
            await dev_plan_clear_fields(db=db, user_id=user_id, dev_plan_id=dev_plan_id)

            # Clear sprint strength/weakness_practice_form_id fields
            sprint = await sprint_get_current(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
            if sprint["sprint_id"] is not None:
              await sprint_clear_fields(db=db, user_id=user_id, sprint_id=sprint["sprint_id"])

            # Clear practices and chosen_practices for certain dev plan id 
            chosen_strength_id = chosen_traits["chosen_strength"]["id"]
            chosen_weakness_id = chosen_traits["chosen_weakness"]["id"]
            await practices_and_chosen_practices_clear_all(db=db, chosen_strength_id=chosen_strength_id, chosen_weakness_id=chosen_weakness_id, dev_plan_id=dev_plan_id, user_id=user_id)
            # Clear 1_STRENGTH/WEAKNESS_PRACTICE_QUESTIONS
            delete_form_and_associations_form_name(db=db, dev_plan_id=dev_plan_id, form_name="1_STRENGTH_PRACTICE_QUESTIONS")
            delete_form_and_associations_form_name(db=db, dev_plan_id=dev_plan_id, form_name="1_WEAKNESS_PRACTICE_QUESTIONS")

            # Clear chosen_traits
            chosen_traits = chosen_traits_clear(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
            # Clear 1_STRENGTH/WEAKNESS_QUESTIONS
            delete_form_and_associations_form_name(db=db, dev_plan_id=dev_plan_id, form_name="1_STRENGTH_QUESTIONS")
            delete_form_and_associations_form_name(db=db, dev_plan_id=dev_plan_id, form_name="1_WEAKNESS_QUESTIONS")  

            # Clear personal_practice_category and chosen_personal_practices for certain dev plan id
            await personal_practice_category_and_chosen_personal_practices_clear_all(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
            # Clear 1_MIND_BODY_QUESTIONS
            delete_form_and_associations_form_name(db=db, dev_plan_id=dev_plan_id, form_name="1_MIND_BODY_QUESTIONS")

            # Clear pending actions
            await pending_actions_clear_all(db=db, user_id=user_id)

    # Schedule the update operation as a background task if 10 additional inputs
    if increment_count(db=db, user_id=user_id):
      background_tasks.add_task(update_ave_std, db)
      
    return { "message": "Initial question answers saved and t-scores computed." }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
