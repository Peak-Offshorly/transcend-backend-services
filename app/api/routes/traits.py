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

@router.get("/all")
async def get_all_traits(db: db_dependency):
  try:
    return traits_get_all(db)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

@router.get("/{id}")
async def get_one_trait(id, db: db_dependency):
  try:
    return traits_get_one(db=db, id=id)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
    
