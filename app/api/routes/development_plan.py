from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.connection import get_db
from app.api.routes.user import firebaseAdminAuth
from app.utils.traits_crud import chosen_traits_get
from app.utils.answers_crud import answers_get_all
from app.utils.practices_crud import chosen_personal_practices_get_all, personal_practice_category_get_one, chosen_practices_get

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/development-plan", tags=["development-plan"])

# Get Development Plan Gantt Chart
@router.get("/gantt-chart-data")
async def get_gantt_chart(sprint_number: int, db: db_dependency, user_id: str = Depends(firebaseAdminAuth)):
  chosen_traits = chosen_traits_get(db=db, user_id=user_id)
  
  chosen_trait_practices = await chosen_practices_get(db=db, user_id=user_id, sprint_number=sprint_number)
  
  recommended_mind_body_category = await personal_practice_category_get_one(db=db, user_id=user_id)

  try:
    return { 
      "chosen_strength": chosen_traits["chosen_strength"],
      "strength_practice": chosen_trait_practices["chosen_strength_practice"],
      "chosen_weakness": chosen_traits["chosen_weakness"],
      "weakness_practice": chosen_trait_practices["chosen_weakness_practice"],
      "mind_body_practice": recommended_mind_body_category
    }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Details of Plan -- for Review Page
@router.get("/review-details")
async def get_review_details(user_id: str, sprint_number: int, db: db_dependency):
  # Strength/Weakness
  chosen_traits = chosen_traits_get(db=db, user_id=user_id)
  
  # Practice for Strength/Weakness
  chosen_trait_practices = await chosen_practices_get(db=db, user_id=user_id, sprint_number=sprint_number)
  # Dev actions for each strength/weakness practice
  strength_form_name = f"{sprint_number}_STRENGTH_PRACTICE_QUESTIONS"
  weakness_form_name = f"{sprint_number}_WEAKNESS_PRACTICE_QUESTIONS"
  strength_practice_dev_actions= await answers_get_all(db=db, user_id=user_id, form_name=strength_form_name, sprint_number=sprint_number)
  weakness_practice_dev_actions= await answers_get_all(db=db, user_id=user_id, form_name=weakness_form_name, sprint_number=sprint_number)
  
  # Mind Body Practice category and Chosen Recommendations
  recommended_mind_body_category = await personal_practice_category_get_one(db=db, user_id=user_id)
  chosen_recommendations = await chosen_personal_practices_get_all(db=db, user_id=user_id, recommended_mind_body_category_id=recommended_mind_body_category.id)

  try:
    return { 
      "chosen_strength": chosen_traits["chosen_strength"],
      "strength_practice": chosen_trait_practices["chosen_strength_practice"],
      "strength_practice_dev_actions": strength_practice_dev_actions,
      "chosen_weakness": chosen_traits["chosen_weakness"],
      "weakness_practice": chosen_trait_practices["chosen_weakness_practice"],
      "weakness_practice_dev_actions": weakness_practice_dev_actions,
      "mind_body_practice": recommended_mind_body_category,
      "mind_body_chosen_recommendations": chosen_recommendations
    }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))