import json
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.schemas.models import DataFormSchema, FormAnswerSchema
from app.database.connection import get_db
from app.utils.forms_crud import mind_body_form_questions_options_get_all, forms_with_questions_options_get_all, forms_create_one
from app.utils.answers_crud import answers_save_one
from app.utils.practices_crud import personal_practice_category_save_one, personal_practice_category_get_one

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/answers", tags=["answers"])

@router.get("/all")
async def answers_get_all(user_id: str, db: db_dependency):
  try:
    return { "message": "answers" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))