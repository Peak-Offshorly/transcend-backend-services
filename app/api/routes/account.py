from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.get("/user")
async def get_user_account():
  try:
    return { "message": "User Account" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
@router.post("/create-user")
async def create_user_account():
  try:
    return { "message": "User Account" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))