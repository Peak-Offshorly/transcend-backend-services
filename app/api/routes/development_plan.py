
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.connection import get_db

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/development-plan", tags=["development-plan"])

@router.get("/gantt-chart/{user_id}")
async def get_questions():
  try:
    return { "message": "Gantt Chart" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))


@router.get("/review-details/{user_id}")
async def get_questions():
  try:
    return { "message": "Review Details" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))