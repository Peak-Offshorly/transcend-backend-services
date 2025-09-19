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
from app.utils.pending_actions_crud import pending_actions_create_one, pending_actions_read, pending_actions_clear_all, pending_actions_create_bulk
from app.ai.helpers.prompts import DevelopmentActionsPrompts
from app.services.user_data_service import user_data_service

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/development-actions", tags=["development-actions"])

import time
@router.post("/get-actions")
async def get_actions(data: DevelopmentActionsSchema, db: db_dependency):
  try:
    user_id = data.user_id
    trait_type = data.trait_type

    # Check for existing actions first
    existing_actions = await pending_actions_read(db=db, user_id=user_id, category=trait_type)

    if existing_actions:
      response = []
      for action in existing_actions:
        response.append({
          "details": action.action
        })
      return {"actions": response}
    
    # Get all user data with using user_data_service (with caching)
    base_data = await user_data_service.get_user_base_data(db=db, user_id=user_id)
    
    # Get cached vectorstore
    vectorstore = user_data_service.get_vectorstore()
    
    # Get trait-specific data
    chosen_trait, trait_practice, _, _ = user_data_service.get_trait_inputs(base_data, trait_type)
    
    # Get documents for the trait and practice
    docs = get_docs(vectorstore=vectorstore, trait=chosen_trait, practice=trait_practice)
    
    # Format context based on trait type
    context_label = "Strength Context" if trait_type == "strength" else "Weakness Context"
    final_docs = f"""
      {context_label}:
      {docs}
    """
    
    # Build AI inputs
    inputs = user_data_service.build_ai_inputs(base_data, trait_type, final_docs)
    
    # Generate actions
    prompt_template = DevelopmentActionsPrompts.initial_generation_prompt()
    response = generate_actions(prompt_template=prompt_template, inputs=inputs)

    # Create actions in bulk for better performance
    action_details = [action["details"] for action in response["actions"]]
    await pending_actions_create_bulk(db=db, user_id=user_id, actions=action_details, category=trait_type)
        
    return response
  except Exception as error:
    raise HTTPException(status_code=500, detail=str(error))
  

@router.post("/regenerate-actions")
async def regenerate_actions(data: DevelopmentActionsSchema, db: db_dependency):
  try:
    user_id = data.user_id
    trait_type = data.trait_type

    # Get existing actions to build previous_actions string
    existing_actions = await pending_actions_read(db=db, user_id=user_id, category=trait_type)
    previous_actions = ""
    if existing_actions:
      for action in existing_actions:
        previous_actions += f"- {action.action}\n"

    # Get all user data using the user_data_service (with caching)
    base_data = await user_data_service.get_user_base_data(db=db, user_id=user_id)
    
    # Get cached vectorstore
    vectorstore = user_data_service.get_vectorstore()
    
    # Get trait-specific data
    chosen_trait, trait_practice, _, _ = user_data_service.get_trait_inputs(base_data, trait_type)
    
    # Get documents for the trait and practice
    docs = get_docs(vectorstore=vectorstore, trait=chosen_trait, practice=trait_practice)
    
    # Format context based on trait type
    context_label = "Strength Context" if trait_type == "strength" else "Weakness Context"
    final_docs = f"""
      {context_label}:
      {docs}
    """
    
    # Build AI inputs with previous actions
    inputs = user_data_service.build_ai_inputs(base_data, trait_type, final_docs, previous_actions)
    
    # Generate actions
    prompt_template = DevelopmentActionsPrompts.regeneration_prompt()
    response = generate_actions(prompt_template=prompt_template, inputs=inputs)

    # Clear existing actions and create new ones in bulk
    await pending_actions_clear_all(db=db, user_id=user_id)
    
    action_details = [action["details"] for action in response["actions"]]
    await pending_actions_create_bulk(db=db, user_id=user_id, actions=action_details, category=trait_type)

    return response
  except Exception as error:
    raise HTTPException(status_code=500, detail=str(error))


@router.post("/clear-actions")
async def clear_actions(user_id:str, db: db_dependency):
  try:
    await pending_actions_clear_all(db=db, user_id=user_id)
  except Exception as error:
    raise HTTPException(status_code=500, detail=str(error))