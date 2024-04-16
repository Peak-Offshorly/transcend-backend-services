
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.connection import get_db

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/personal-practices", tags=["personal-practices"])

# Get Mind Body Practices Questions
@router.get("/questions/{user_id}")
async def get_questions():
  try:
    return { "message": "Guide Qeuestions" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Post Save Mind Body Practices Answers 
@router.post("/save-answers/{user_id}")
async def save_answers():
  try:
    return { "message": "Development Actions Saved" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Mind Body Practice Recommendation
@router.get("/recommendations/{user_id}")
async def get_recommendations():
  try:
    return { "message": "Get Recommendations" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Post Save Mind Body Practice Chosen Recommendation (min 1, max 2 answers)
@router.post("/save-selected-recommendations/{user_id}")
async def save_selected_recommendations():
  try:
    return { "message": "Save Selected Recommendations" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))