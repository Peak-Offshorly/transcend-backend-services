import json
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from app.schemas.models import DataFormSchema, FormAnswerSchema, ChosenPersonalPracticesSchema
from app.database.connection import get_db
from app.utils.dev_plan_crud import dev_plan_create_get_one, dev_plan_update_personal_practice_category
from app.utils.forms_crud import mind_body_form_questions_options_get_all, forms_with_questions_options_get_all, forms_create_one
from app.utils.answers_crud import answers_save_one
from app.utils.practices_crud import (
    personal_practice_category_save_one, 
    personal_practice_category_get_one, 
    chosen_personal_practices_clear_existing,
    chosen_personal_practices_save_one,
    chosen_personal_practices_get_all
)

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
    dev_plan = await dev_plan_create_get_one(db=db, user_id=user_id)
    dev_plan_id = dev_plan["dev_plan_id"]
    form_exists = forms_with_questions_options_get_all(db=db, name=form_name, user_id=user_id, dev_plan_id=dev_plan_id)
    
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
      dev_plan_id=dev_plan_id
    )

    await forms_create_one(db=db, form=form_data)
    return forms_with_questions_options_get_all(db, name=form_name, user_id=user_id, dev_plan_id=dev_plan_id)
  
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
    dev_plan = await dev_plan_create_get_one(db=db, user_id=user_id)
    dev_plan_id = dev_plan["dev_plan_id"]
    category = await personal_practice_category_save_one(
      db=db,
      name=recommended_category,
      user_id=user_id,
      dev_plan_id=dev_plan_id
    )

    # Update current dev plan personal practice category id
    await dev_plan_update_personal_practice_category(
      db=db, 
      user_id=user_id, 
      personal_practice_category_id=category["personal_practice_category_id"]
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

    dev_plan = await dev_plan_create_get_one(db=db, user_id=user_id)
    dev_plan_id = dev_plan["dev_plan_id"]
    category = await personal_practice_category_get_one(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
    recommendations = mind_body_practices[category.name]
    
    return { 
      "recommended_mind_body_category_id": category.id,
      "recommended_mind_body_category": category.name,
      "recommendations": recommendations
    }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Post Save Mind Body Practice Chosen Recommendation (min 1, max 2 answers)
@router.post("/save-selected-recommendations")
async def save_selected_recommendations(chosen_personal_practices: ChosenPersonalPracticesSchema, db: db_dependency):
  user_id = chosen_personal_practices.user_id
  recommended_mind_body_category_id = chosen_personal_practices.recommended_mind_body_category_id
  chosen_recommendations = chosen_personal_practices.chosen_practices
  try:
    # Save selected recommendations
    if len(chosen_recommendations) <= 2:
      # Clear if there are existing mind body practices in DB
      await chosen_personal_practices_clear_existing(db=db, user_id=user_id, recommended_mind_body_category_id=recommended_mind_body_category_id)

      for recommendation in chosen_recommendations:
        await chosen_personal_practices_save_one(db=db, user_id=user_id, name=recommendation.name, recommended_mind_body_category_id=recommended_mind_body_category_id)
    
    else:
      return { "error": "Cannot save more than 2 recommendations." }

    return { "message": "Selected Mind-body recommendations saved." }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
@router.get("/get-selected-recommendations")
async def get_selected_recommendations(user_id: str, db: db_dependency):
  try:
    dev_plan = await dev_plan_create_get_one(db=db, user_id=user_id)
    dev_plan_id = dev_plan["dev_plan_id"]
    category = await personal_practice_category_get_one(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
    chosen_recommendations = await chosen_personal_practices_get_all(db=db, user_id=user_id, recommended_mind_body_category_id=category.id)

    return { 
      "recommended_mind_body_category": category.name,
      "chosen_recommendations": chosen_recommendations
    }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
