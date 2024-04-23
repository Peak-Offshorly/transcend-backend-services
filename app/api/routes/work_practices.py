
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

@router.post("/create-form")
async def create_form(data: DataFormSchema, db: db_dependency):
  try:
    form_name = data.form_name
    user_id = data.user_id

    # Create an instance of FormSchema
    form_data = FormSchema(
        name=form_name,
        user_id=user_id,
        questions=[
            QuestionSchema(
                name="Question 1",
                option_type="multiple_choice",
                options=[
                    OptionSchema(
                        name="A. I continuously work on my professional development and share my learnings.",
                        type="multiple_choice"
                    ),
                    OptionSchema(
                        name="B. I prioritize long-term goals over short-term gains.",
                        type="multiple_choice"
                    ),
                    OptionSchema(
                        name="C. I prioritize well-being through healthy routines related to sleep, exercise, and diet.",
                        type="multiple_choice"
                    )
                ]
            ),
            QuestionSchema(
                name="Question 2",
                option_type="multiple_choice",
                options=[
                    OptionSchema(
                        name="A. I actively listen to understand others' viewpoints.",
                        type="multiple_choice"
                    ),
                    OptionSchema(
                        name="B. I provide constructive feedback regularly and in a supportive manner.",
                        type="multiple_choice"
                    ),
                    OptionSchema(
                        name="C. I provide a safe space for team members to express grievances.",
                        type="multiple_choice"
                    )
                ]
            )
        ]
    )

    print("data", data)
    form = forms_create_one(db, form=form_data)

    return form
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

@router.get("/get-form")
async def get_form(data: DataFormSchema, db: db_dependency):
  try:
    name = data.form_name
    user_id = data.user_id
    #form = forms_with_questions_get_one(db, name=name, user_id=user_id)
    form = forms_with_questions_options_get_all(db, name=name, user_id=user_id)

    return form
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))


# Post Save Development Actions (Direct user input, at most 3)
@router.get("/development-actions/{user_id}")
async def get_development_actions():
  try:
    return { "message": "Development Actions Created" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Written Development Actions
@router.post("/save-development-actions/{user_id}")
async def save_development_actions():
  try:
    return { "message": "Development Actions Saved" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# not in current estimates -- not sure if the user can update it in the next loop of the dev plan
@router.post("/update-development-actions/{user_id}")
async def update_development_actions():
  try:
    return { "message": "Development Actions Updated" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))