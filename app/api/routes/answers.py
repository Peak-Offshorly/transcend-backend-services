from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.connection import get_db
from app.utils.dev_plan_crud import dev_plan_create_get_one
from app.utils.answers_crud import answers_all_forms_get_all, initial_questions_answers_all_forms_get_all
from app.utils.practices_crud import chosen_practices_get, personal_practice_category_get_one, chosen_personal_practices_get_all

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/answers", tags=["answers"])

@router.get("/all")
async def answers_get_all(user_id: str, db: db_dependency):
  try:
    dev_plan = await dev_plan_create_get_one(db=db, user_id=user_id)
    dev_plan_id = dev_plan["dev_plan_id"]
    intial_form_answers = await initial_questions_answers_all_forms_get_all(db=db, user_id=user_id)
    forms_answers = intial_form_answers + await answers_all_forms_get_all(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
    
    # Chosen strength/weakness practices
    chosen_trait_practices_1 = await chosen_practices_get(db=db, user_id=user_id, sprint_number=1)
    if len(chosen_trait_practices_1['chosen_strength_practice']) == 0 :
      chosen_trait_practices_1['chosen_strength_practice'] = None
    if len(chosen_trait_practices_1['chosen_weakness_practice']) == 0:
      chosen_trait_practices_1['chosen_weakness_practice'] = None
    
    chosen_trait_practices_2 = await chosen_practices_get(db=db, user_id=user_id, sprint_number=2) 
    if len(chosen_trait_practices_2['chosen_strength_practice']) == 0 :
      chosen_trait_practices_2['chosen_strength_practice'] = None
    if len(chosen_trait_practices_2['chosen_weakness_practice']) == 0:
      chosen_trait_practices_2['chosen_weakness_practice'] = None

    # Mind Body Practice category and Chosen Recommendations
    recommended_mind_body_category = await personal_practice_category_get_one(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
    if recommended_mind_body_category:
      chosen_recommendations = await chosen_personal_practices_get_all(db=db, user_id=user_id, recommended_mind_body_category_id=recommended_mind_body_category.id)
    else:
      chosen_recommendations = None
    
    return {
      "forms_and_answers": forms_answers,
      "practices_sprint_1": {
        "strength_practice": chosen_trait_practices_1["chosen_strength_practice"][0].name if chosen_trait_practices_1["chosen_strength_practice"] else None,
        "weakness_practice": chosen_trait_practices_1["chosen_weakness_practice"][0].name if chosen_trait_practices_2["chosen_weakness_practice"] else None,
      },
      "practices_sprint_2": {
        "strength_practice": chosen_trait_practices_2["chosen_strength_practice"][0].name if chosen_trait_practices_2["chosen_strength_practice"] else None,
        "weakness_practice": chosen_trait_practices_2["chosen_weakness_practice"][0].name if chosen_trait_practices_2["chosen_weakness_practice"] else None
      },
      "mind_body_practice": recommended_mind_body_category,
      "mind_body_chosen_recommendations": chosen_recommendations
    } 
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))