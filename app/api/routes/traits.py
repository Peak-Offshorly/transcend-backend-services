import json
from uuid import UUID
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from app.schemas.models import ChosenTraitsSchema, FormAnswerSchema, PracticeSchema, ChosenPracticesSchema
from app.database.connection import get_db
from app.firebase.utils import verify_token
from app.utils.users_crud import get_one_user_id
from app.utils.dates_crud import compute_second_sprint_dates
from app.utils.answers_crud import answers_save_one, are_matching_answers
from app.utils.pending_actions_crud import pending_actions_clear_all
from app.utils.dev_plan_crud import(
    dev_plan_create_get_one, 
    dev_plan_update_chosen_traits, 
    dev_plan_update_sprint, 
    dev_plan_update_chosen_strength_practice, 
    dev_plan_update_chosen_weakness_practice, 
    dev_plan_clear_fields
)
from app.utils.forms_crud import(
    form_questions_options_get_all, 
    forms_create_one, 
    forms_with_questions_options_get_all, 
    forms_with_questions_options_sprint_id_get_all,
    delete_form_and_associations_form_name
)
from app.utils.sprints_crud import(
    sprint_create_get_one, 
    sprint_update_strength_form_id, 
    sprint_update_weakness_form_id, 
    sprint_update_second_sprint_dates, 
    get_sprint_start_end_date_sprint_number, 
    sprint_get_current,
    sprint_clear_fields
)
from app.utils.practices_crud import(
  practice_save_one,
  practices_by_trait_type_get,
  practices_by_trait_type_get_2nd_sprint,
  practices_clear_existing,
  chosen_practices_save_one,
  practices_and_chosen_practices_clear_all,
  personal_practice_category_and_chosen_personal_practices_clear_all
) 
from app.utils.traits_crud import(
    traits_get_top_bottom_five,
    chosen_traits_create,
    chosen_traits_get,
    chosen_traits_clear
)

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/traits", tags=["traits"])

# Get Traits (Strengths and Weaknesses with the Scores)
@router.get("/all-strengths-weaknesses")
async def get_strengths_weaknesses(user_id: str, db: db_dependency, token = Depends(verify_token)):
    query_user = get_one_user_id(db=db, user_id=user_id)
    token_user = get_one_user_id(db=db, user_id=token)

    # Check if requested user exists
    if not query_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested user not found"
        )

    # Check if token user exists
    if not token_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    # Users can always access their own data
    if token == user_id:
        try:
            return traits_get_top_bottom_five(db=db, user_id=user_id)
        except Exception as error:
            raise HTTPException(status_code=400, detail=str(error))

    # Admin can only access data of users in their company
    if token_user.user_type == 'admin':
        if query_user.company_id == token_user.company_id:
            try:
                return traits_get_top_bottom_five(db=db, user_id=user_id)
            except Exception as error:
                raise HTTPException(status_code=400, detail=str(error))
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin can only access data of users in their company"
            )

    # Non-admin users trying to access other users' data
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can only access your own data"
    )
  
# Post Save Chosen Strength and Weakness
@router.post("/save-strength-weakness")
async def save_traits_chosen(chosen_traits: ChosenTraitsSchema, db: db_dependency, token = Depends(verify_token)):
  user_id = chosen_traits.user_id
  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )
  
  trait_data = {
      "strength": chosen_traits.strength,
      "weakness": chosen_traits.weakness
  }
  try:
    # Make dev plan for user
    dev_plan = await dev_plan_create_get_one(user_id=user_id, db=db) 
    dev_plan_id = dev_plan["dev_plan_id"]

    # ----Clear succeeding forms/practices/traits
    chosen_traits = chosen_traits_get(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
    if chosen_traits:
        if chosen_traits["chosen_strength"]["name"] != trait_data["strength"].name or chosen_traits["chosen_weakness"]["name"] != trait_data["weakness"].name:
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

          # Iterate over strength and weakness
          for trait_type, data in trait_data.items():
            trait_id = data.id
            trait_name = data.name
            t_score = data.t_score
          
            # Create Form for certain trait
            trait_form = await create_trait_form(db=db, user_id=user_id, trait=trait_name, dev_plan_id=dev_plan_id, trait_type=trait_type)

            # Create ChosenTrait entry, attach form id for certain trait Form
            chosen_traits_create(
              db=db, 
              user_id=user_id, 
              form_id=trait_form["form_id"],
              trait_id=trait_id, 
              trait_name=trait_name, 
              t_score=t_score, 
              trait_type=trait_type,
              dev_plan_id=dev_plan_id
            )
          
          chosen_traits = chosen_traits_get(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
          chosen_strength_id = chosen_traits["chosen_strength"]["id"]
          chosen_weakness_id = chosen_traits["chosen_weakness"]["id"]
          await dev_plan_update_chosen_traits(user_id=user_id, chosen_strength_id=chosen_strength_id, chosen_weakness_id=chosen_weakness_id, db=db)
      
    else:
      # Iterate over strength and weakness
      for trait_type, data in trait_data.items():
        trait_id = data.id
        trait_name = data.name
        t_score = data.t_score

        # Create Form for certain trait
        trait_form = await create_trait_form(db=db, user_id=user_id, trait=trait_name, dev_plan_id=dev_plan_id, trait_type=trait_type)
        # Create ChosenTrait entry, attach form id for certain trait Form
        chosen_traits_create(
          db=db, 
          user_id=user_id, 
          form_id=trait_form["form_id"],
          trait_id=trait_id, 
          trait_name=trait_name, 
          t_score=t_score, 
          trait_type=trait_type,
          dev_plan_id=dev_plan_id
        )

      chosen_traits = chosen_traits_get(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
      chosen_strength_id = chosen_traits["chosen_strength"]["id"]
      chosen_weakness_id = chosen_traits["chosen_weakness"]["id"]
      await dev_plan_update_chosen_traits(user_id=user_id, chosen_strength_id=chosen_strength_id, chosen_weakness_id=chosen_weakness_id, db=db)
      

    return { "message": "Strength and Weakness added and Forms created." }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
# Create Form questions and options for trait; used in Post Save Chosen Strength and Weakness
async def create_trait_form(user_id: str, trait: str, trait_type: str, dev_plan_id: UUID, db: db_dependency):
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
      trait_name=trait,
      dev_plan_id=dev_plan_id
    )

    trait_form = await forms_create_one(db=db, form=form_data)

    return trait_form
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Chosen Strength and Weakness
@router.get("/get-strength-weakness")
async def get_traits_chosen(user_id: str, db: db_dependency, token = Depends(verify_token)):
  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )
  
  try:
    dev_plan = await dev_plan_create_get_one(user_id=user_id, db=db)
    return chosen_traits_get(db=db, user_id=user_id, dev_plan_id=dev_plan["dev_plan_id"])
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
# Get Form questions and options for trait strength/weakness
@router.get("/get-trait-questions")
async def get_trait_questions(user_id: str, form_name: str, db: db_dependency, token = Depends(verify_token)):
  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )
  
  try:
    dev_plan = await dev_plan_create_get_one(user_id=user_id, db=db)
    return forms_with_questions_options_get_all(db, name=form_name, user_id=user_id, dev_plan_id = dev_plan["dev_plan_id"])
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Post Save Followup Trait Answers; would have calculations based on answers to determine which practices to recommend
@router.post("/save-trait-questions-answers")
async def save_traits_answers(answers: FormAnswerSchema, db: db_dependency, token = Depends(verify_token)):
  user_id = answers.user_id
  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )
  
  form_id = answers.form_id
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
    
    # Check "To a Large Extent" and "To the Fullest Extent"answers if needed
    if len(recommended_practices) < 5 and (extent_answers["To a Large Extent"] or extent_answers["To the Fullest Extent"]):
      # Sort the answers by rank
      sorted_answers_3 = sorted(extent_answers["To a Large Extent"] + extent_answers["To the Fullest Extent"], key=lambda x: x.question_rank)
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
async def get_trait_practices(user_id: str, trait_type: str, db: db_dependency, token = Depends(verify_token)):
  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )
  
  try:
    dev_plan = await dev_plan_create_get_one(user_id=user_id, db=db)
    
    # Create sprint  
    sprint = await sprint_create_get_one(db=db, user_id=user_id, dev_plan_id=dev_plan["dev_plan_id"])
    
    # If 2nd sprint, set 2 random practices to is_recommended to True
    if sprint["sprint_number"] == 2:
      return await practices_by_trait_type_get_2nd_sprint(db=db, user_id=user_id, trait_type=trait_type, dev_plan_id=dev_plan["dev_plan_id"])
    
    return await practices_by_trait_type_get(db=db, user_id=user_id, trait_type=trait_type, dev_plan_id=dev_plan["dev_plan_id"])
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
# Post Save Trait Practices - SEPERATE FOR STRENGTH AND WEAKNESS
@router.post("/save-strength-practice")
async def save_chosen_strength_practice(chosen_practices: ChosenPracticesSchema, db: db_dependency, token = Depends(verify_token)):
  user_id = chosen_practices.user_id
  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )
  
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

  # Get current dev plan 
  dev_plan = await dev_plan_create_get_one(user_id=user_id, db=db)

  # Determine which sprint you are in
  sprint = await sprint_create_get_one(db=db, user_id=user_id, dev_plan_id=dev_plan["dev_plan_id"])
  sprint_number = sprint["sprint_number"] 
  sprint_id = sprint["sprint_id"] 
  form_name = f"{sprint_number}_STRENGTH_PRACTICE_QUESTIONS"

  # Update current dev plan with sprint id
  await dev_plan_update_sprint(db=db, user_id=user_id, sprint_number=sprint_number, sprint_id=sprint_id)
  
  # If 2nd sprint, add start_date and end_date of second sprint
  if sprint_number == 2:
    sprint_1 = await get_sprint_start_end_date_sprint_number(db=db, user_id=user_id, sprint_number=1, dev_plan_id=dev_plan["dev_plan_id"])
    sprint_2_dates = await compute_second_sprint_dates(start_to_mid_date=sprint_1["end_date"], end_date=dev_plan["end_date"])
    await sprint_update_second_sprint_dates(
      db=db, 
      user_id=user_id, 
      sprint_id=sprint_id, 
      dev_plan_id=dev_plan["dev_plan_id"],
      start_date=sprint_2_dates["start_date"],
      end_date=sprint_2_dates["end_date"]
    )

  try: 
    practice_id = strength_practice.id
    practice_name = strength_practice.name
    chosen_trait_id = strength_practice.chosen_trait_id
    
    form_exists = forms_with_questions_options_sprint_id_get_all(db=db, name=form_name, user_id=user_id, sprint_id=sprint_id)
    if form_exists:
      form_id = form_exists.id
    else:
      # Create the Form; user input Form of max 3 written inputs/answers
      form_data = form_questions_options_get_all(
        user_id=user_id,
        form_name=form_name,
        option_type="text_field",
        category="PRACTICES_QS",
        questions=questions,
        options=options,
        ranks=ranks,
        sprint_number=sprint_number,
        sprint_id=sprint_id,
        dev_plan_id=dev_plan["dev_plan_id"]
      )
      practice_form = await forms_create_one(db=db, form=form_data)
      form_id = practice_form["form_id"]

    # Update Sprint with strength practice form_id
    await sprint_update_strength_form_id(db=db, user_id=user_id, sprint_id=sprint_id, strength_form_id=form_id)

    # Create ChosenPractice entry with form id
    chosen_practice = chosen_practices_save_one(
      db=db,
      user_id=user_id,
      form_id=form_id,
      name=practice_name,
      practice_id=practice_id,
      chosen_trait_id=chosen_trait_id,
      sprint_number=sprint_number,
      sprint_id=sprint_id,
      dev_plan_id=dev_plan["dev_plan_id"]
    )

    # Update dev plan chosen strength practice id
    await dev_plan_update_chosen_strength_practice(
      user_id=user_id, 
      sprint_number=sprint_number, 
      chosen_strength_id=chosen_practice["chosen_practice_id"],
      db=db
    )

    return { "message": "Chosen Strength Practice saved and Forms created." }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

@router.post("/save-weakness-practice")
async def save_chosen_weakness_practice(chosen_practices: ChosenPracticesSchema, db: db_dependency, token = Depends(verify_token)):
  user_id = chosen_practices.user_id
  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )

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

  # Get current dev plan 
  dev_plan = await dev_plan_create_get_one(user_id=user_id, db=db)

  # Determine which sprint you are in
  sprint = await sprint_create_get_one(db=db, user_id=user_id, dev_plan_id=dev_plan["dev_plan_id"])
  sprint_number = sprint["sprint_number"] 
  sprint_id = sprint["sprint_id"] 
  form_name = f"{sprint_number}_WEAKNESS_PRACTICE_QUESTIONS"

  # Update current dev plan with sprint id
  await dev_plan_update_sprint(db=db, user_id=user_id, sprint_number=sprint_number, sprint_id=sprint_id) 

  try: 
    practice_id = weakness_practice.id
    practice_name = weakness_practice.name
    chosen_trait_id = weakness_practice.chosen_trait_id
    
    form_exists = forms_with_questions_options_sprint_id_get_all(db=db, name=form_name, user_id=user_id, sprint_id=sprint_id)
    if form_exists:
      form_id = form_exists.id
    else:
      # Create the Form; user input Form of max 3 written inputs/answers
      form_data = form_questions_options_get_all(
        user_id=user_id,
        form_name=form_name,
        option_type="text_field",
        category="PRACTICES_QS",
        questions=questions,
        options=options,
        ranks=ranks,
        sprint_number=sprint_number,
        sprint_id=sprint_id,
        dev_plan_id=dev_plan["dev_plan_id"]
      )
      practice_form = await forms_create_one(db=db, form=form_data)
      form_id = practice_form["form_id"]

    # Update Sprint with weakness practice form_id
    await sprint_update_weakness_form_id(db=db, user_id=user_id, sprint_id=sprint_id, weakness_form_id=form_id)

    # Create ChosenPractice entry with form id
    chosen_practice = chosen_practices_save_one(
      db=db,
      user_id=user_id,
      form_id=form_id,
      name=practice_name,
      practice_id=practice_id,
      chosen_trait_id=chosen_trait_id,
      sprint_number=sprint_number,
      sprint_id=sprint_id,
      dev_plan_id=dev_plan["dev_plan_id"]
    )

    # Update dev plan chosen weakness practice id
    await dev_plan_update_chosen_weakness_practice(
      user_id=user_id, 
      sprint_number=sprint_number, 
      chosen_weakness_id=chosen_practice["chosen_practice_id"],
      db=db
    )

    return { "message": "Chosen Weakness Practice saved and Forms created." }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
    
