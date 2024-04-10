
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.connection import get_db

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/personal-practices", tags=["personal-practices"])

@router.get("/questions/{user_id}")
async def get_questions():
  try:
    return { "message": "Guide Qeuestions" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
@router.post("/save-answers/{user_id}")
async def save_answers():
  try:
    return { "message": "Development Actions Saved" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

@router.get("/recommendations/{user_id}")
async def get_recommendations():
  try:
    return { "message": "Get Recommendations" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

@router.post("/save-selected-recommendations/{user_id}")
async def save_selected_recommendations():
  try:
    return { "message": "Save Selected Recommendations" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))