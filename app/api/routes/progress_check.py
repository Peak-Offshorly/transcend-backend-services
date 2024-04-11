from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.connection import get_db

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/progress-check", tags=["progress-check"])

# Get Written Development Actions as Questions (Strength, Weakness)
@router.get("/development-progress-questions/{user_id}")
async def get_development_progress_questions():
  try:
    return { "message": "Guide Qeuestions" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Post Save Answers for Written Development Actions as Questions (Strength, Weakness)
@router.post("/save-development-progress-answers/{user_id}")
async def save_development_progress_answers():
  try:
    return { "message": "Development Actions Saved" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))