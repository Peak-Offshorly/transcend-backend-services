from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import Annotated
from app.schemas.models import UserColleagueEmailsSchema, DataFormSchema
from app.email.send_email import send_email_background, send_email_async
from app.database.connection import get_db
from app.utils.users_crud import get_one_user_id
from app.utils.dev_plan_crud import dev_plan_create_get_one
from app.utils.user_colleagues_crud import colleague_email_save_one, user_colleagues_get_all, user_colleagues_clear_all

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/colleague-feedback", tags=["colleague-feedback"])

# Save Colleague Emails
@router.post("/save-emails")
async def save_colleague_emails(data: UserColleagueEmailsSchema, db: db_dependency):
  user_id = data.user_id
  emails = data.emails
  try:
    # Get current dev plan
    dev_plan = await dev_plan_create_get_one(user_id=user_id, db=db)
    dev_plan_id=dev_plan["dev_plan_id"]
    
    if len(emails) > 5: 
      return { "message": "Cannot save more than 5 emails." }

    await user_colleagues_clear_all(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
    for email in emails:
      await colleague_email_save_one(db=db, user_id=user_id, email=email, dev_plan_id=dev_plan_id)
      
    return { "message": "Colleague emails saved." }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

@router.post("/send-initial-emails")
async def send_initial_emails(db: db_dependency, background_tasks: BackgroundTasks, data: DataFormSchema):
  user_id = data.user_id
  try:
    # Get current dev plan
    dev_plan = await dev_plan_create_get_one(user_id=user_id, db=db)
    dev_plan_id=dev_plan["dev_plan_id"]

    user = get_one_user_id(db=db, user_id=user_id)
    user_colleagues = await user_colleagues_get_all(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
    user_email_href = f"https://mail.google.com/mail/u/0/?view=cm&fs=1&tf=1&to={user.email}"
    
    for colleague in user_colleagues:
      body = { 
        "colleague_email": colleague.email, 
        "user_name": user.first_name,
        "user_email_href": user_email_href
      }

      send_email_background(
        background_tasks=background_tasks, 
        body=body, 
        email_to=colleague.email, 
        subject="Test - Initial Colleague Email"
      )
      
    return { "message": "Colleague Initial emails sent." }
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
