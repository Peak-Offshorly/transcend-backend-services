from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from app.firebase.session import firebase, auth
from app.database.connection import get_db
from app.utils.traits_crud import(
    traits_get_all,
    traits_get_one
)

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/traits", tags=["traits"])

# Get Traits (Strengths and Weaknesses with the Scores)
@router.get("/all")
async def get_all_traits(db: db_dependency):
  try:
    return traits_get_all(db)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
# Post Save Chosen Strength and Weakness
@router.post("/save-chosen")
async def save_traits_chosen(db: db_dependency):
  try:
    return None
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Chosen Strength and Weakness
@router.get("/{id}")
async def get_one_trait(id, db: db_dependency):
  try:
    return traits_get_one(db=db, id=id)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
# Get Followup Trait Questions (Should work the same for both strength and weakness); id=id of trait or user(?)
@router.get("/get-questions/{id}")
async def get_trait_questions(db: db_dependency):
  try:
    return None
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
# Post Save Followup Trait Answers; would have calculations based on answers to determine which practices to recommend; id=id of trait(?)
@router.post("/save-answers/{id}")
async def save_traits_answers(db: db_dependency):
  try:
    return None
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Trait Practice; 
@router.get("/get-practices/{id}")
async def get_trait_practices(id, db: db_dependency):
  try:
    return None
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Post Save Trait Practices 
@router.post("/save-practices-answers/{id}")
async def save_trait_practices_answers(id, db: db_dependency):
  try:
    return None
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

    
