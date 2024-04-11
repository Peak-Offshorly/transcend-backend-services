
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.connection import get_db

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/work-practices", tags=["work-practices"])

@router.get("/questions/{user_id}")
async def get_questions():
  try:
    return { "message": "Guide Qeuestions" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

@router.get("/development-actions/{user_id}")
async def get_development_actions():
  try:
    return { "message": "Development Actions Created" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
    
@router.post("/save-development-actions/{user_id}")
async def save_development_actions():
  try:
    return { "message": "Development Actions Saved" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

@router.post("/update-development-actions/{user_id}")
async def update_development_actions():
  try:
    return { "message": "Development Actions Updated" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))