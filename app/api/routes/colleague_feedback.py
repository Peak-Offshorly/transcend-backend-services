
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.connection import get_db

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/colleague-feedback", tags=["colleague-feedback"])

@router.get("/questions")
async def get_questions():
  try:
    return { "message": "Colleague Feedback Questions" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

@router.get("/{id}")
async def get_one_colleague_feedback():
  try:
    return { "message": "One Colleague Feedback" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

@router.get("/all")
async def get_all_colleague_feedbacks():
  try:
    return { "message": "All Colleague Feedback" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

@router.post("/save/{id}")
async def save_colleague_feedback():
  try:
    return { "message": "Colleague Feedback Saved" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error)) 

@router.get("/status/{user_id}")
async def get_colleague_feedback_status():
  try:
    return { "message": "Colleague Feedback Status" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
