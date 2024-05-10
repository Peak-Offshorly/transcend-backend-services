from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.connection import get_db
from app.utils.answers_crud import answers_all_forms_get_all

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/answers", tags=["answers"])

@router.get("/all")
async def answers_get_all(user_id: str, db: db_dependency):
  try:
    return await answers_all_forms_get_all(db=db, user_id=user_id)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))