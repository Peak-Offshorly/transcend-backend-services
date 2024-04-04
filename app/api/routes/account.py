from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.firebase.session import firebase, auth

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
    user = auth.create_user(
      email = "test@gmail.com",
      password = "password"
    )
    
    return JSONResponse(content={"message":  f"User account created successfuly for user {user.uid}"},
                        status_code=200)
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))