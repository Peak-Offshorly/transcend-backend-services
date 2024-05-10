
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.connection import get_db
from app.utils.traits_crud import chosen_traits_get
from app.utils.practices_crud import practices_by_trait_type_get, chosen_personal_practices_get_all, personal_practice_category_get_one, chosen_practices_get

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/development-plan", tags=["development-plan"])

# Get Development Plan Gantt Chart
@router.get("/gantt-chart-data")
async def get_gantt_chart(user_id: str, db: db_dependency):
  chosen_traits = chosen_traits_get(db=db, user_id=user_id)
  
  chosen_trait_practices = await chosen_practices_get(db=db, user_id=user_id, sprint_number=1)
  
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
@router.get("/review-details/{user_id}")
async def get_review_details():
  try:
    return { "message": "Review Details" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))