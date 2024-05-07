import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.schemas.models import DataFormSchema
from app.database.connection import get_db
from app.utils.forms_crud import mind_body_form_questions_options_get_all, forms_with_questions_options_get_all, forms_create_one

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/personal-practices", tags=["personal-practices"])

# Get Mind Body Practices Questions
@router.post("/get-form")
async def create_get_personal_practices_form(data: DataFormSchema, db: db_dependency):
  form_name = data.form_name
  user_id = data.user_id

  questions=[]
  weights=[]
  options = []
  categories = []
  try:
    form_exists = forms_with_questions_options_get_all(db=db, name=form_name, user_id=user_id)
    
    # return if Form exists already
    if form_exists:
      return form_exists
    
    with open("app/utils/data/mind_body_questions.json", "r") as file:
      mind_body_questions = json.load(file)

    for category, questions_data in mind_body_questions.items():
      for q_data in questions_data:
        question = q_data['question']
        weight = q_data['weight']
        q_options = q_data['options']

        # Append data to respective arrays
        questions.append(question)
        weights.append(weight)
        options.append(q_options)
        categories.append(category)

    # Slight changes:
    # Rank is the Weight for the Question model
    # Type is the 1-4/1-5 Points for each option for the Option model
    form_data = mind_body_form_questions_options_get_all(
      user_id=user_id,
      form_name=form_name,
      option_type="multiple_choice",
      categories=categories,
      questions=questions,
      options=options,
      weights=weights,
    )

    await forms_create_one(db=db, form=form_data)
    return forms_with_questions_options_get_all(db, name=form_name, user_id=user_id)
  
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Post Save Mind Body Practices Answers 
@router.post("/save-answers/{user_id}")
async def save_answers():
  try:
    return { "message": "Development Actions Saved" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Mind Body Practice Recommendation
@router.get("/recommendations/{user_id}")
async def get_recommendations():
  try:
    return { "message": "Get Recommendations" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Post Save Mind Body Practice Chosen Recommendation (min 1, max 2 answers)
@router.post("/save-selected-recommendations/{user_id}")
async def save_selected_recommendations():
  try:
    return { "message": "Save Selected Recommendations" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))