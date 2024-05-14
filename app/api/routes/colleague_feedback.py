from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from app.schemas.models import UserColleagueEmailsSchema
from app.database.connection import get_db
from app.utils.user_colleagues_crud import colleague_email_save_one

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/colleague-feedback", tags=["colleague-feedback"])

# Save Colleague Emails
@router.post("/save-emails")
async def save_colleague_emails(data: UserColleagueEmailsSchema, db: db_dependency):
  user_id = data.user_id
  emails = data.emails
  try:
    for email in emails:
      await colleague_email_save_one(db=db, user_id=user_id, email=email)
      
    return { "message": "Colleague emails saved." }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Colleague Feedback Questions
@router.get("/questions")
async def get_questions():
  try:
    return { "message": "Colleague Feedback Questions" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Individual Colleague Feedback
@router.get("/{id}")
async def get_one_colleague_feedback():
  try:
    return { "message": "One Colleague Feedback" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get All Colleague Feedbacks
@router.get("/all")
async def get_all_colleague_feedbacks():
  try:
    return { "message": "All Colleague Feedback" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Post Save Colleague Feedback
@router.post("/save/{id}")
async def save_colleague_feedback():
  try:
    return { "message": "Colleague Feedback Saved" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error)) 

# Get Colleague Feedback Status
@router.get("/status/{user_id}")
async def get_colleague_feedback_status():
  try:
    return { "message": "Colleague Feedback Status" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
