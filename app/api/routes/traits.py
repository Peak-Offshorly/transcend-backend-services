import json
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Annotated
from app.schemas.models import ChosenTraitsSchema, FormAnswerSchema, PracticeSchema, ChosenPracticesSchema
from app.database.connection import get_db
from app.utils.forms_crud import form_questions_options_get_all, forms_create_one, forms_with_questions_options_get_all
from app.utils.answers_crud import answers_save_one
from app.utils.practices_crud import(
  practice_save_one, 
  practices_by_trait_type_get,
  practices_clear_existing,
  chosen_practices_get_max_sprint, 
  chosen_practices_save_one
) 
from app.utils.traits_crud import(
    traits_get_top_bottom_five,
    chosen_traits_create,
    chosen_traits_get
)

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/traits", tags=["traits"])

# Get Traits (Strengths and Weaknesses with the Scores)
@router.get("/all-strengths-weaknesses")
async def get_strengths_weaknesses(user_id: str, db: db_dependency):
  try:
    return traits_get_top_bottom_five(db=db, user_id=user_id)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
# Post Save Chosen Strength and Weakness
@router.post("/save-strength-weakness")
async def save_traits_chosen(chosen_traits: ChosenTraitsSchema, db: db_dependency):
  user_id = chosen_traits.user_id
  trait_data = {
      "strength": chosen_traits.strength,
      "weakness": chosen_traits.weakness
  }
  try:
    # Iterate over strength and weakness
    for trait_type, data in trait_data.items():
      trait_id = data.id
      trait_name = data.name
      t_score = data.t_score
    
      # Create Form for certain trait
      trait_form = await create_trait_form(db=db, user_id=user_id, trait=trait_name, trait_type=trait_type)

      # Create ChosenTrait entry, attach form id for certain trait Form
      chosen_traits_create(
        db=db, 
        user_id=user_id, 
        form_id=trait_form["form_id"],
        trait_id=trait_id, 
        trait_name=trait_name, 
        t_score=t_score, 
        trait_type=trait_type
      )

    return { "message": "Strength and Weakness added and Forms created." }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
# Create Form questions and options for trait; used in Post Save Chosen Strength and Weakness
async def create_trait_form(user_id: str, trait: str, trait_type: str, db: db_dependency):
  form_name = f"1_{trait_type.upper()}_QUESTIONS" 
  questions=[]
  ranks=[]
  options = [
    "Not at All",
    "To a Small Extent",
    "To a Moderate Extent",
    "To a Large Extent",
    "To the Fullest Extent"
  ]

  try:
    with open("app/utils/data/practice_followup.json", "r") as file:
      traits_questions = json.load(file)

    for rank, question in traits_questions.get(trait, {}).items():
      questions.append(question)
      ranks.append(rank)
    
    form_data = form_questions_options_get_all(
      user_id=user_id,
      form_name=form_name,
      option_type="likert_scale",
      category="TRAITS_QS",
      questions=questions,
      options=options,
      ranks=ranks,
      trait_name=trait
    )

    trait_form = await forms_create_one(db=db, form=form_data)

    return trait_form
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Chosen Strength and Weakness
@router.get("/get-strength-weakness")
async def get_traits_chosen(user_id: str, db: db_dependency):
  try:
    return chosen_traits_get(db=db, user_id=user_id)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
# Get Form questions and options for trait strength/weakness
@router.get("/get-trait-questions")
async def get_trait_questions(user_id: str, form_name: str, db: db_dependency):
  try:
    return forms_with_questions_options_get_all(db, name=form_name, user_id=user_id)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Post Save Followup Trait Answers; would have calculations based on answers to determine which practices to recommend
@router.post("/save-trait-questions-answers")
async def save_traits_answers(answers: FormAnswerSchema, db: db_dependency):
  form_id = answers.form_id
  user_id = answers.user_id
  recommended_practices = []

  # Dictionary to store answers categorized by extent
  extent_answers = defaultdict(list)

  try:
    for answer in answers.answers:
      # Add all answers in DB and in extent_answers dict
      await answers_save_one(
        db=db,
        form_id=form_id,
        question_id=answer.question_id,
        option_id=answer.option_id,
        answer=answer.answer
      )
      extent_answers[answer.answer].append(answer)

    # First, sort the "Not at All" or "To a Small Extent" answers  by rank
    sorted_answers_1 = sorted(extent_answers["Not at All"] + extent_answers["To a Small Extent"], key=lambda x: x.question_rank)
    # Select the first 5 practices as recommended
    recommended_practices = sorted_answers_1[:5]

    # Check "To a Moderate Extent" answers if practices are still less than 5
    if len(recommended_practices) < 5 and extent_answers["To a Moderate Extent"]:
      # Sort the answers by rank
      sorted_answers_2 = sorted(extent_answers["To a Moderate Extent"], key=lambda x: x.question_rank)
      # Add to recommended practices until we have 5
      recommended_practices += sorted_answers_2[:5 - len(recommended_practices)]
    
    # Check "To a Large Extent" answers if needed
    if len(recommended_practices) < 5 and extent_answers["To a Large Extent"]:
      # Sort the answers by rank
      sorted_answers_3 = sorted(extent_answers["To a Large Extent"], key=lambda x: x.question_rank)
      # Add to recommended practices until we have 5
      recommended_practices += sorted_answers_3[:5 - len(recommended_practices)]

    # Clear if there are existing practices in DB
    await practices_clear_existing(db=db, user_id=user_id, question_id=recommended_practices[0].question_id)

    # Add each recommended practice in DB
    for practice in recommended_practices:
      practice_data = PracticeSchema(
        user_id=user_id,
        question_id=practice.question_id
      )
      
      await practice_save_one(
        db=db,
        practice=practice_data
      )
    
    return {'message': 'Answers and Recommended Practices saved.'}
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Trait Practices
@router.get("/get-trait-practices")
async def get_trait_practices(user_id: str, trait_type: str, db: db_dependency):
  try:
    return await practices_by_trait_type_get(db=db, user_id=user_id, trait_type=trait_type)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
# Post Save Trait Practices - SEPERATE FOR STRENGTH AND WEAKNESS
@router.post("/save-strength-practice")
async def save_chosen_strength_practice(chosen_practices: ChosenPracticesSchema, db: db_dependency):
  user_id = chosen_practices.user_id
  strength_practice = chosen_practices.strength_practice

  # Form questions, ranks and options at most 3; placeholders only
  questions=[
    "DEVELOPMENT_ACTION_1",
    "DEVELOPMENT_ACTION_2",
    "DEVELOPMENT_ACTION_3"
  ]
  ranks=[0,0,0]
  options=[
    "DEVELOPMENT_ACTION_CHOICE_1"
  ]

  # Determine which sprint you are in
  sprint = await chosen_practices_get_max_sprint(db=db, user_id=user_id) or 1 
  form_name = f"{sprint}_STRENGTH_PRACTICE_QUESTIONS" 

  try: 
    practice_id = strength_practice.id
    practice_name = strength_practice.name
    chosen_trait_id = strength_practice.chosen_trait_id
    # Create the Form; user input Form of max 3 written inputs/answers
    form_data = form_questions_options_get_all(
      user_id=user_id,
      form_name=form_name,
      option_type="text_field",
      category="PRACTICES_QS",
      questions=questions,
      options=options,
      ranks=ranks,
      sprint_number=sprint
    )
    practice_form = await forms_create_one(db=db, form=form_data)
    # Create ChosenPractice entry with form id
    chosen_practices_save_one(
      db=db,
      user_id=user_id,
      form_id=practice_form["form_id"],
      name=practice_name,
      practice_id=practice_id,
      chosen_trait_id=chosen_trait_id,
      sprint_number=sprint
    )

    return { "message": "Chosen Strength Practice saved and Forms created." }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

@router.post("/save-weakness-practice")
async def save_chosen_weakness_practice(chosen_practices: ChosenPracticesSchema, db: db_dependency):
  user_id = chosen_practices.user_id
  weakness_practice = chosen_practices.weakness_practice

  # Form questions, ranks and options at most 3; placeholders only
  questions=[
    "DEVELOPMENT_ACTION_1",
    "DEVELOPMENT_ACTION_2",
    "DEVELOPMENT_ACTION_3"
  ]
  ranks=[0,0,0]
  options=[
    "DEVELOPMENT_ACTION_CHOICE_1"
  ]

  # Determine which sprint you are in
  sprint = await chosen_practices_get_max_sprint(db=db, user_id=user_id) or 1 
  form_name = f"{sprint}_WEAKNESS_PRACTICE_QUESTIONS" 

  try: 
    practice_id = weakness_practice.id
    practice_name = weakness_practice.name
    chosen_trait_id = weakness_practice.chosen_trait_id
    # Create the Form; user input Form of max 3 written inputs/answers
    form_data = form_questions_options_get_all(
      user_id=user_id,
      form_name=form_name,
      option_type="text_field",
      category="PRACTICES_QS",
      questions=questions,
      options=options,
      ranks=ranks,
      sprint_number=sprint
    )
    practice_form = await forms_create_one(db=db, form=form_data)
    # Create ChosenPractice entry with form id
    chosen_practices_save_one(
      db=db,
      user_id=user_id,
      form_id=practice_form["form_id"],
      name=practice_name,
      practice_id=practice_id,
      chosen_trait_id=chosen_trait_id,
      sprint_number=sprint
    )

    return { "message": "Chosen Weakness Practice saved and Forms created." }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
    
