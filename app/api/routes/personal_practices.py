import json
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.schemas.models import DataFormSchema, FormAnswerSchema
from app.database.connection import get_db
from app.utils.forms_crud import mind_body_form_questions_options_get_all, forms_with_questions_options_get_all, forms_create_one
from app.utils.answers_crud import answers_save_one
from app.utils.practices_crud import personal_practice_category_save_one, personal_practice_category_get_one

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
@router.post("/save-form-answers")
async def save_answers(answers: FormAnswerSchema, db: db_dependency):
  form_id = answers.form_id
  user_id = answers.user_id

  category_scores = defaultdict(int)
  category_total_possible_points = {
    'EXERCISE': 19,
    'NUTRITION': 8,
    'SLEEP': 10,
    'STRESS REDUCTION': 12,
    'ROUTINES': 18
  }

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

      # Calculate the score for each answer; option_type would be the option_point, question_rank would be the weight
      score = int(answer.option_type) * int(answer.question_rank)
      # Add the score to the respective category
      category_scores[answer.question_category] += score
    
    # Calculate the average score for each category
    category_avg_scores = {}
    for category, score in category_scores.items():
        count = category_total_possible_points[category]
        category_avg_scores[category] = score / count 
    # Find the category with the lowest average score
    recommended_category = min(category_avg_scores, key=category_avg_scores.get)

    # Save recommended category in DB
    await personal_practice_category_save_one(
      db=db,
      name=recommended_category,
      user_id=user_id
    )

    return {
      "message": "Mind-body Practice area saved and calculations done.", 
      "recommended_mind_body_category": recommended_category 
    }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Mind Body Practice Recommendation
@router.get("/recommendations")
async def get_recommendations(user_id: str, db: db_dependency):
  try:
    with open("app/utils/data/mind_body_practices.json", "r") as file:
      mind_body_practices = json.load(file)

    category = await personal_practice_category_get_one(db=db, user_id=user_id)
    recommendations = mind_body_practices[category.name]
    
    return { 
      "recommended_mind_body_category": category.name,
      "recommendations": recommendations
    }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Post Save Mind Body Practice Chosen Recommendation (min 1, max 2 answers)
@router.post("/save-selected-recommendations/{user_id}")
async def save_selected_recommendations():
  try:
    return { "message": "Save Selected Recommendations" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))