from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.firebase.session import firebase, auth
from app.database.connection import get_db
from app.utils.traits_crud import(
    traits_get_all,
    traits_get_one,
    traits_get_top_bottom_five
)

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/traits", tags=["traits"])

# Get Traits (Strengths and Weaknesses with the Scores)
@router.get("/all")
async def get_top_bottom_five_traits(request: Request ,db: db_dependency):
  payload = await request.json()
  user_id = payload["user_id"]
  try:
    return traits_get_top_bottom_five(db=db, user_id=user_id)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
# Post Save Chosen Strength and Weakness
@router.post("/save-chosen")
async def save_traits_chosen(request: Request, db: db_dependency):
  payload = await request.json()
  try:
    return None
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Chosen Strength and Weakness
@router.get("/{user_id}/{trait_id}")
async def get_one_trait(user_id, trait_id, db: db_dependency):
  try:
    return traits_get_one(db=db, trait_id=id)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
# Get Followup Trait Questions (Should work the same for both strength and weakness)
@router.get("/get-questions/{trait_id}")
async def get_trait_questions(trait_id, db: db_dependency):
  try:
    return None
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
# Post Save Followup Trait Answers; would have calculations based on answers to determine which practices to recommend
@router.post("/save-answers/{user_id}")
async def save_traits_answers(user_id, db: db_dependency):
  try:
    return None
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Trait Practice;
@router.get("/get-practices/{user_id}")
async def get_trait_practices(id, db: db_dependency):
  try:
    return None
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Post Save Trait Practices 
@router.post("/save-practices-answers/{user_id}")
async def save_trait_practices_answers(user_id, db: db_dependency):
  try:
    return None
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

    
