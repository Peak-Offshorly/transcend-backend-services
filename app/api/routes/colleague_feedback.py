from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import Annotated
from app.schemas.models import UserColleagueEmailsSchema, DataFormSchema
from app.email.send_email import send_email_background, send_email_async
from app.database.connection import get_db
from app.utils.sprints_crud import sprint_get_current
from app.utils.dates_crud import compute_colleague_message_dates
from app.utils.users_crud import get_one_user_id
from app.utils.dev_plan_crud import dev_plan_create_get_one
from app.utils.user_colleagues_crud import colleague_email_save_one, user_colleagues_get_all, user_colleagues_clear_all, user_colleagues_add_dates
from app.api.routes.development_plan import get_review_details 

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
    dev_plan_id = dev_plan["dev_plan_id"]
    start_date = dev_plan["start_date"]
    end_date = dev_plan["end_date"]

    # Compute dates for Colleague messages
    colleague_message_dates = await compute_colleague_message_dates(start_date=start_date, end_date=end_date)
    
    if len(emails) > 5: 
      return { "message": "Cannot save more than 5 emails." }

    await user_colleagues_clear_all(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
    for email in emails:
      await colleague_email_save_one(db=db, user_id=user_id, email=email, dev_plan_id=dev_plan_id)
      await user_colleagues_add_dates(
        db=db, 
        user_id=user_id, 
        dev_plan_id=dev_plan_id,
        week_5_date=colleague_message_dates["week_5"][0],
        week_9_date=colleague_message_dates["week_9"][0],
        week_12_date=colleague_message_dates["week_12"][0]
      )
      
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
    current_sprint = await sprint_get_current(user_id=user_id, db=db, dev_plan_id=dev_plan_id)
    dev_plan_details = await get_review_details(user_id=user_id, sprint_number=current_sprint["sprint_number"], db=db)

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
