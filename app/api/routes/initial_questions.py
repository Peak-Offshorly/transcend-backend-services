from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.firebase.session import firebase, auth
from app.database.connection import get_db
# from app.utils.initial_questions_crud import(
#     initial_questions_get_all,
#     initial_questions_get_one
# )

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/initial-questions", tags=["initial-questions"])

# Get Initial Questions
@router.get("/all")
async def get_all_initial_questions(db: db_dependency):
  try:
    # return initial_questions_get_all(db)
    return {"message": "get all"}
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

@router.get("/{initial_question_id}")
async def get_one_initial_question(initial_question_id, db: db_dependency):
  try:
    # return initial_questions_get_one(db=db, id=id)
    return {"message": "get one"}
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
# Post Save Initial Answers; would have calculations based on chosen answers
@router.post("/save-answers/{user_id}")
async def save_initial_questions_answers(user_id, db: db_dependency):
  try:
    return None
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))