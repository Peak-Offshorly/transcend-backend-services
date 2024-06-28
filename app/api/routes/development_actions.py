from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from app.schemas.models import DevelopmentActionsSchema
from app.database.connection import get_db
from app.ai.helpers.get_vectorstore import get_vectorstore
from app.ai.helpers.get_documents import get_docs
from app.ai.helpers.chains import generate_actions, check_user_input
from app.ai.data.format_initial_questions import get_initial_questions_with_answers
from app.ai.data.traits_practices import get_ten_traits, get_chosen_traits, get_chosen_practices
from app.utils.answers_crud import initial_questions_answers_all_forms_get_all
from app.utils.practices_crud import chosen_practices_get
from app.utils.dev_plan_crud import dev_plan_get_current
from app.utils.traits_crud import traits_get_top_bottom_five, chosen_traits_get
from app.utils.sprints_crud import sprint_get_current
from app.utils.users_crud import get_user_company_details
from app.utils.pending_actions_crud import pending_actions_create_one, pending_actions_read, pending_actions_clear_all
from app.ai.helpers.prompts import DevelopmentActionsPrompts

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/development-actions", tags=["development-actions"])

@router.post("/get-actions")
async def get_actions(data: DevelopmentActionsSchema, db: db_dependency):
  try:
    user_id = data.user_id
    trait_type = data.trait_type

    existing_actions = await pending_actions_read(db=db, user_id=user_id, category=trait_type)

    if existing_actions:
      response = []
      for action in existing_actions:
        response.append({
          "details": action.action
        })

      return {"actions": response}
    else:
      company_details = get_user_company_details(db=db, user_id=user_id)

      valid_data = check_user_input(company_size=company_details.company_size, industry=company_details.industry, employee_role=company_details.role, role_description=company_details.role_description)

      company_size = valid_data['company_size']
      industry = valid_data['industry']
      employee_role = valid_data['employee_role']
      role_description = valid_data['role_description']

      vectorstore = get_vectorstore(index_name="peak-ai")

      # Getting initial questions with answers
      user_answers = await initial_questions_answers_all_forms_get_all(db=db, user_id=user_id)
      answers_list = user_answers[0].answers
      initial_questions_with_answers = get_initial_questions_with_answers(answers_list)

      # Getting top and bottom five
      ten_traits = traits_get_top_bottom_five(db=db, user_id=user_id)
      strengths, weaknesses = get_ten_traits(ten_traits)

      dev_plan = await dev_plan_get_current(db=db, user_id=user_id)
      dev_plan_id = dev_plan["dev_plan_id"]

      # Getting chosen traits
      chosen_traits = chosen_traits_get(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
      chosen_strength, chosen_weakness = get_chosen_traits(chosen_traits)

      current_sprint = await sprint_get_current(db=db, user_id=user_id, dev_plan_id=dev_plan_id)

      chosen_trait_practices_1 = await chosen_practices_get(db=db, user_id=user_id, sprint_number=current_sprint['sprint_number'], dev_plan_id=dev_plan_id)
      strength_practice, weakness_practice = get_chosen_practices(chosen_trait_practices_1)

      response = ""
      prompt_template = DevelopmentActionsPrompts.initial_generation_prompt()
      if trait_type == "strength":
        # print("Strengths", strengths)
        # print("Chosen Strength: ", chosen_strength)
        # print("Chosen Practice: ", strength_practice)
        docs = get_docs(vectorstore=vectorstore, trait=chosen_strength, practice=strength_practice)
        final_docs = f"""
          Strength Context:
          {docs}
        """

        inputs = {
          "type": trait_type,
          "context": final_docs,
          "initial_questions": initial_questions_with_answers,
          "five_traits": ",".join(strengths),
          "chosen_trait": chosen_strength,
          "trait_practice": strength_practice,
          "company_size": company_size,
          "industry": industry,
          "employee_role": employee_role,
          "role_description": role_description
        }
              
        response = generate_actions(prompt_template=prompt_template, inputs=inputs)
      elif trait_type == "weakness":
        # print("Weaknesses", weaknesses)
        # print("Chosen Weakness: ", chosen_weakness)
        # print("Chosen Practice: ", weakness_practice)
        docs = get_docs(vectorstore=vectorstore, trait=chosen_weakness, practice=weakness_practice)
        final_docs = f"""
          Weakness Context:
          {docs}
        """

        inputs = {
          "type": trait_type,
          "context": final_docs,
          "initial_questions": initial_questions_with_answers,
          "five_traits": ",".join(weaknesses),
          "chosen_trait": chosen_weakness,
          "trait_practice": weakness_practice,
          "company_size": company_size,
          "industry": industry,
          "employee_role": employee_role,
          "role_description": role_description
        }
        
        response = generate_actions(prompt_template=prompt_template, inputs=inputs)

      #create one for each action
      for action in response["actions"]:
        print("action", action)
        await pending_actions_create_one(db=db, user_id=user_id, action=action["details"], category=trait_type)
        
      return response
  except Exception as error:
    raise HTTPException(status_code=500, detail=str(error))
  

@router.post("/regenerate-actions")
async def regenerate_actions(data: DevelopmentActionsSchema, db: db_dependency):
  try:
    user_id = data.user_id
    trait_type = data.trait_type

    existing_actions = await pending_actions_read(db=db, user_id=user_id, category=trait_type)
    previous_actions = ""

    if existing_actions:
      for action in existing_actions:
        previous_actions += f"- {action.action}\n"

    company_details = get_user_company_details(db=db, user_id=user_id)

    valid_data = check_user_input(company_size=company_details.company_size, industry=company_details.industry, employee_role=company_details.role, role_description=company_details.role_description)

    company_size = valid_data['company_size']
    industry = valid_data['industry']
    employee_role = valid_data['employee_role']
    role_description = valid_data['role_description']

    vectorstore = get_vectorstore(index_name="peak-ai")

    # Getting initial questions with answers
    user_answers = await initial_questions_answers_all_forms_get_all(db=db, user_id=user_id)
    answers_list = user_answers[0].answers
    initial_questions_with_answers = get_initial_questions_with_answers(answers_list)

    # Getting top and bottom five
    ten_traits = traits_get_top_bottom_five(db=db, user_id=user_id)
    strengths, weaknesses = get_ten_traits(ten_traits)

    dev_plan = await dev_plan_get_current(db=db, user_id=user_id)
    dev_plan_id = dev_plan["dev_plan_id"]

    # Getting chosen traits
    chosen_traits = chosen_traits_get(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
    chosen_strength, chosen_weakness = get_chosen_traits(chosen_traits)

    current_sprint = await sprint_get_current(db=db, user_id=user_id, dev_plan_id=dev_plan_id)

    chosen_trait_practices_1 = await chosen_practices_get(db=db, user_id=user_id, sprint_number=current_sprint['sprint_number'], dev_plan_id=dev_plan_id)
    strength_practice, weakness_practice = get_chosen_practices(chosen_trait_practices_1)

    response = ""
    prompt_template = DevelopmentActionsPrompts.regeneration_prompt()
    if trait_type == "strength":
      docs = get_docs(vectorstore=vectorstore, trait=chosen_strength, practice=strength_practice)
      final_docs = f"""
        Strength Context:
        {docs}
      """

      inputs = {
        "type": trait_type,
        "context": final_docs,
        "initial_questions": initial_questions_with_answers,
        "five_traits": ",".join(strengths),
        "chosen_trait": chosen_strength,
        "trait_practice": strength_practice,
        "company_size": company_size,
        "industry": industry,
        "employee_role": employee_role,
        "role_description": role_description,
        "previous_actions": previous_actions
      }
            
      response = generate_actions(prompt_template=prompt_template, inputs=inputs)
    elif trait_type == "weakness":
      docs = get_docs(vectorstore=vectorstore, trait=chosen_weakness, practice=weakness_practice)
      final_docs = f"""
        Weakness Context:
        {docs}
      """

      inputs = {
        "type": trait_type,
        "context": final_docs,
        "initial_questions": initial_questions_with_answers,
        "five_traits": ",".join(weaknesses),
        "chosen_trait": chosen_weakness,
        "trait_practice": weakness_practice,
        "company_size": company_size,
        "industry": industry,
        "employee_role": employee_role,
        "role_description": role_description,
        "previous_actions": previous_actions
      }
      
      response = generate_actions(prompt_template=prompt_template, inputs=inputs)

    #clear pending actions
    await pending_actions_clear_all(db=db, user_id=user_id)

    #create one for each action
    for action in response["actions"]:
      await pending_actions_create_one(db=db, user_id=user_id, action=action["details"], category=trait_type)
      
    return response
  except Exception as error:
    raise HTTPException(status_code=500, detail=str(error))

@router.post("/clear-actions")
async def clear_actions(user_id:str, db: db_dependency):
  try:
    await pending_actions_clear_all(db=db, user_id=user_id)
  except Exception as error:
    raise HTTPException(status_code=500, detail=str(error))