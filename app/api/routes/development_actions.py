from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from app.schemas.models import DevelopmentActionsSchema
from app.database.connection import get_db
from app.ai.helpers.get_vectorstore import get_vectorstore
from app.ai.helpers.get_documents import get_docs
from app.ai.helpers.chains import generate_actions
from app.ai.data.format_initial_questions import get_initial_questions_with_answers
from app.ai.data.traits_practices import get_ten_traits, get_chosen_traits, get_chosen_practices
from app.utils.answers_crud import initial_questions_answers_all_forms_get_all
from app.utils.practices_crud import chosen_practices_get
from app.utils.dev_plan_crud import dev_plan_create_get_one
from app.utils.traits_crud import traits_get_top_bottom_five, chosen_traits_get

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/development-actions", tags=["development-actions"])

@router.post("/get-actions")
async def get_actions(data: DevelopmentActionsSchema, db: db_dependency):
  user_id = data.user_id
  company_size = data.company_size
  industry = data.industry
  employee_role = data.employee_role
  role_description = data.role_description
  trait_type = data.trait_type

  #todo: add data checker -- avoid prompt injection

  try:
    vectorstore = get_vectorstore(index_name="peak-ai")
    # retriever = vectorstore.as_retriever(search_type="mmr")
    # retriever = vectorstore.as_retriever()
    # retriever = vectorstore.as_retriever(
    #   search_type="similarity_score_threshold", search_kwargs={"score_threshold": 0.7, "k": 10}
    # )

    # Getting initial questions with answers
    user_answers = await initial_questions_answers_all_forms_get_all(db=db, user_id=user_id)
    answers_list = user_answers[0].answers
    initial_questions_with_answers = get_initial_questions_with_answers(answers_list)

    # Getting top and bottom five
    ten_traits = traits_get_top_bottom_five(db=db, user_id=user_id)
    strengths, weaknesses = get_ten_traits(ten_traits)

    dev_plan = await dev_plan_create_get_one(db=db, user_id=user_id)
    dev_plan_id = dev_plan["dev_plan_id"]

    # Getting chosen traits
    chosen_traits = chosen_traits_get(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
    chosen_strength, chosen_weakness = get_chosen_traits(chosen_traits)

    # Getting chosen practices, sprint 1 (might change, get function from backend)
    chosen_trait_practices_1 = await chosen_practices_get(db=db, user_id=user_id, sprint_number=1, dev_plan_id=dev_plan_id)
    strength_practice, weakness_practice = get_chosen_practices(chosen_trait_practices_1)
    
    strength_docs = get_docs(vectorstore=vectorstore, input_data=chosen_strength)
    weakness_docs = get_docs(vectorstore=vectorstore, input_data=chosen_weakness)

    final_docs = f"""
      Strength Context
      {strength_docs}

      Weakness Context
      {weakness_docs}
    """

    response = generate_actions(final_docs, initial_questions_with_answers, ",".join(strengths), ",".join(weaknesses), chosen_strength, chosen_weakness, strength_practice, weakness_practice, company_size, industry, employee_role, role_description)

    return { "response": response}
  except Exception as error:
    raise HTTPException(status_code=500, detail=str(error))