from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import Annotated
from app.schemas.models import UserColleagueEmailsSchema, DataFormSchema, UserColleagueSurveyAnswersSchema
from app.email.send_email import send_email_background
from app.database.connection import get_db
from app.utils.sprints_crud import sprint_get_current
from app.utils.dates_crud import compute_colleague_message_dates
from app.utils.users_crud import get_one_user_id
from app.utils.traits_crud import chosen_traits_get
from app.utils.dev_plan_crud import dev_plan_create_get_one
from app.utils.user_colleagues_crud import colleague_email_save_one, user_colleagues_get_all, user_colleagues_clear_all, user_colleagues_add_dates, user_colleagues_get_one_survey_token
from app.utils.user_colleagues_survey_crud import survey_save_one
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
        subject="Test - Initial Colleague Email",
        template_name="sample-inline.html"
      )
      
    return { "message": "Colleague Initial emails sent." }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))

# Get Colleague Feedback Questions
@router.get("/questions")
async def get_questions(survey_token: str, db: db_dependency):
  try:
    user_colleague = await user_colleagues_get_one_survey_token(db=db, survey_token=survey_token)
    
    if user_colleague.survey_completed:
      raise HTTPException(status_code=400, detail="Survey already completed")
    
    user = get_one_user_id(db=db, user_id=user_colleague.user_id)
    chosen_traits = chosen_traits_get(db=db, user_id=user_colleague.user_id, dev_plan_id=user_colleague.development_plan_id)
    strength = chosen_traits["chosen_strength"]["name"]
    weakness = chosen_traits["chosen_weakness"]["name"]
    
    # Questions and options
    q1 = f"Over the past 12 weeks, has {user.first_name} become a more (or less) effective leader?"
    q2 = f"Over the past 12 weeks, has {user.first_name} become more (or less) effective in the area of {strength}?"
    q3 = f"Over the past 12 weeks has {user.first_name} become more (or less) effective in the area of {weakness}?"
    q4 = f"What is {user.first_name} doing that is particularly effective?"
    q5 = f"What could {user.first_name} do to be even more effective?"
    integer_options = [-3, -2, -1, 0, 1, 2, 3]

    return {
      "user_colleague_id": user_colleague.id,
      "user_id": user_colleague.user_id,
      "development_plan_id": user_colleague.development_plan_id,
      "q1": q1,
      "q1_options": integer_options,
      "q2": q2,
      "q2_options": integer_options,
      "q3": q3,
      "q3_options": integer_options,
      "q4" : q4,
      "q5" : q5
    }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
# Post Save Colleague Feedback
@router.post("/save")
async def save_colleague_feedback(data: UserColleagueSurveyAnswersSchema, db: db_dependency):
  user_colleague_id = data.user_colleague_id
  q1_answer = data.q1_answer
  q2_answer = data.q2_answer
  q3_answer = data.q3_answer
  q4_answer = data.q4_answer
  q5_answer = data.q5_answer
  try:
    return await survey_save_one(
      db=db,
      user_colleague_id=user_colleague_id,
      q1_answer=q1_answer,
      q2_answer=q2_answer,
      q3_answer=q3_answer,
      q4_answer=q4_answer,
      q5_answer=q5_answer
    ) 
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error)) 

# Get Colleague Feedback Status
@router.get("/status/{user_id}")
async def get_colleague_feedback_status():
  try:
    return { "message": "Colleague Feedback Status" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))