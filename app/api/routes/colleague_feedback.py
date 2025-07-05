from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session
from typing import Annotated
from collections import Counter
from app.schemas.models import UserColleagueEmailsSchema, DataFormSchema, UserColleagueSurveyAnswersSchema, UserColleaguesStatusSchema
from app.email.send_email import send_email_background
from app.database.connection import get_db
from app.firebase.utils import verify_token
from app.utils.sprints_crud import sprint_get_current
from app.utils.dates_crud import compute_colleague_message_dates
from app.utils.users_crud import get_one_user_id
from app.utils.traits_crud import chosen_traits_get
from app.utils.dev_plan_crud import dev_plan_create_get_one
from app.utils.user_colleagues_survey_crud import survey_save_one, survey_get_all
from app.api.routes.development_plan import get_review_details
from app.utils.user_colleagues_crud import (
  colleague_email_save_one, 
  user_colleagues_get_all, 
  user_colleagues_clear_all, 
  user_colleagues_add_dates, 
  user_colleagues_get_one_survey_token, 
  user_colleagues_count, 
  user_colleagues_survey_completed,
  user_colleagues_get_dates
)
from app.email.colleague_emails import user_colleague_week_12_emails_trigger
from app.email.test_emails import send_all_test_emails


db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/colleague-feedback", tags=["colleague-feedback"])

# Save Colleague Emails
@router.post("/save-emails")
async def save_colleague_emails(data: UserColleagueEmailsSchema, db: db_dependency, token = Depends(verify_token)):
  user_id = data.user_id
  emails = data.emails

  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )
  
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
async def send_initial_emails(db: db_dependency, background_tasks: BackgroundTasks, data: DataFormSchema, token = Depends(verify_token)):
  user_id = data.user_id

  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )

  try:
    # Get current dev plan
    dev_plan = await dev_plan_create_get_one(user_id=user_id, db=db)
    dev_plan_id=dev_plan["dev_plan_id"]
    current_sprint = await sprint_get_current(user_id=user_id, db=db, dev_plan_id=dev_plan_id)
    dev_plan_details = await get_review_details(user_id=user_id, sprint_number=current_sprint["sprint_number"], db=db)

    user = get_one_user_id(db=db, user_id=user_id)
    user_colleagues = await user_colleagues_get_all(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
    user_email_href = f"mailto:{user.email}"
    
    for colleague in user_colleagues:
      colleague_email = colleague.email.split("@")
      body = { 
        "colleague_email": colleague_email[0], 
        "user_name": user.first_name,
        "user_email_href": user_email_href,
        "strength": dev_plan_details["chosen_strength"]["name"],
        "weakness": dev_plan_details["chosen_weakness"]["name"],
        "strength_practice": dev_plan_details["strength_practice"][0].name,
        "weakness_practice": dev_plan_details["weakness_practice"][0].name,
        "strength_practice_dev_actions": dev_plan_details["strength_practice_dev_actions"],
        "weakness_practice_dev_actions": dev_plan_details["weakness_practice_dev_actions"],
        "recommended_category": dev_plan_details["mind_body_practice"].name,
        "chosen_personal_practices": dev_plan_details["mind_body_chosen_recommendations"],
        "sprint_number": current_sprint["sprint_number"]
      }

      send_email_background(
        background_tasks=background_tasks, 
        body=body, 
        email_to=colleague.email, 
        subject=f"Leadership Development Plan - Would Love Your Thoughts",
        template_name="initial-colleague-email.html",
        reply_to=user.email
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
    # UPDATE integration of week 4 cycle Changed from 12 weeks to 4 weeks
    q1 = f"Over the past 4 weeks, has {user.first_name} become a more (or less) effective leader?"
    q2 = f"Over the past 4 weeks, has {user.first_name} become more (or less) effective in the area of {strength}?"
    q3 = f"Over the past 4 weeks has {user.first_name} become more (or less) effective in the area of {weakness}?"
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
@router.get("/status")
async def get_colleague_feedback_status(user_id: str, db: db_dependency, token = Depends(verify_token)):
  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )

  try:
    # Get current dev plan
    dev_plan = await dev_plan_create_get_one(user_id=user_id, db=db)
    dev_plan_id=dev_plan["dev_plan_id"]

    # Count of user colleagues and user colleagues with completed survey
    count_user_colleagues = await user_colleagues_count(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
    count_user_colleagues_completed_survey = await user_colleagues_survey_completed(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
    
    user_colleagues = await user_colleagues_get_all(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
    colleagues_emails_and_status = [UserColleaguesStatusSchema.model_validate(colleague) for colleague in user_colleagues]

    return { 
      "colleagues_invited_count": count_user_colleagues,
      "colleagues_survey_completed_count": count_user_colleagues_completed_survey,
      "colleagues_emails_and_status": colleagues_emails_and_status
    }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
# Get All Colleague Feedback for user
@router.get("/all")
async def get_colleague_feedback_summary(user_id: str, db: db_dependency, token = Depends(verify_token)):
  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )

  try:
    # Get current dev plan
    dev_plan = await dev_plan_create_get_one(user_id=user_id, db=db)
    dev_plan_id = dev_plan["dev_plan_id"]

    user_colleague_surveys = await survey_get_all(db=db, user_id=user_id, dev_plan_id=dev_plan_id)

    # Initialize counters and lists
    effective_leader_counter = Counter()
    effective_strength_area_counter = Counter()
    effective_weakness_area_counter = Counter()
    particularly_effective_list = []
    more_effective_list = []  

    # Process each survey
    for survey in user_colleague_surveys:
        effective_leader_counter[survey.effective_leader] += 1
        effective_strength_area_counter[survey.effective_strength_area] += 1
        effective_weakness_area_counter[survey.effective_weakness_area] += 1
        particularly_effective_list.append(survey.particularly_effective)
        more_effective_list.append(survey.more_effective)

    user = get_one_user_id(db=db, user_id=user_id)
    chosen_traits = chosen_traits_get(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
    strength = chosen_traits["chosen_strength"]["name"]
    weakness = chosen_traits["chosen_weakness"]["name"]
    # UPDATED integration of week 4 cycle: Changed from 12 weeks to 4 weeks
    q1 = f"Over the past 4 weeks, has {user.first_name} become a more (or less) effective leader?"
    q2 = f"Over the past 4 weeks, has {user.first_name} become more (or less) effective in the area of {strength}?"
    q3 = f"Over the past 4 weeks has {user.first_name} become more (or less) effective in the area of {weakness}?"
    q4 = f"What is {user.first_name} doing that is particularly effective?"
    q5 = f"What could {user.first_name} do to be even more effective?"

    return {
            q1 : effective_leader_counter,
            q2 : effective_strength_area_counter,
            q3 : effective_weakness_area_counter,
            q4 : particularly_effective_list,
            q5 : more_effective_list
        }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  
# Get Colleague Feedback Dates
@router.get("/dates")
async def get_colleague_feedback_dates(user_id: str, db: db_dependency, token = Depends(verify_token)):
  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )

  try:
    # Get current dev plan
    dev_plan = await dev_plan_create_get_one(user_id=user_id, db=db)
    dev_plan_id = dev_plan["dev_plan_id"]

    colleague_message_dates = await user_colleagues_get_dates(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
    
    if colleague_message_dates:
      return {
        "colleague_message_week_5_date": colleague_message_dates["week_5"],
        "colleague_message_week_9_date": colleague_message_dates["week_9"],
        "colleague_message_week_12_date": colleague_message_dates["week_12"]
      }
    
    return { "message": "No saved colleagues for user" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error)) 

#----FOR UAT OF JEREMY SETUP
# Get Colleague Feedback Dates
@router.post("/send-colleague-survey")
async def send_colleague_survey(db: db_dependency, data: DataFormSchema, background_tasks: BackgroundTasks):
  user_id = data.user_id
  try:
    response = await user_colleague_week_12_emails_trigger(db=db, user_id=user_id, background_tasks=background_tasks)

    return { 
      "message": response
    } 
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error)) 
#----FOR UAT OF JEREMY SETUP



@router.post("/test-all-emails")
async def test_all_emails(
    db: db_dependency, 
    background_tasks: BackgroundTasks, 
    data: DataFormSchema, 
    colleague_email: str,
    token = Depends(verify_token)
):
    user_id = data.user_id
    
    if token != user_id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action."
        )
    
    try:
        result = await send_all_test_emails(
            db=db,
            test_user_id=user_id,
            test_colleague_email=colleague_email,
            background_tasks=background_tasks
        )
        return result
        
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
    
# EXACT EMAIL COPY (CURRENTLY NOT USED)
@router.post("/preview-initial-email")
async def preview_initial_email(db: db_dependency, data: DataFormSchema, token = Depends(verify_token)):
  """
  Preview the initial colleague email without sending it.
  Returns the rendered HTML content that would be sent to colleagues.
  """
  user_id = data.user_id

  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )

  try:
    # Get current dev plan
    dev_plan = await dev_plan_create_get_one(user_id=user_id, db=db)
    dev_plan_id=dev_plan["dev_plan_id"]
    current_sprint = await sprint_get_current(user_id=user_id, db=db, dev_plan_id=dev_plan_id)
    dev_plan_details = await get_review_details(user_id=user_id, sprint_number=current_sprint["sprint_number"], db=db)

    user = get_one_user_id(db=db, user_id=user_id)
    user_email_href = f"mailto:{user.email}"
    
    # Use placeholder email for preview
    colleague_email = "colleague@example.com".split("@")
    
    # Build the same body structure as the actual send email endpoint
    body = { 
      "colleague_email": colleague_email[0], 
      "user_name": user.first_name,
      "user_email_href": user_email_href,
      "strength": dev_plan_details["chosen_strength"]["name"],
      "weakness": dev_plan_details["chosen_weakness"]["name"],
      "strength_practice": dev_plan_details["strength_practice"][0].name,
      "weakness_practice": dev_plan_details["weakness_practice"][0].name,
      "strength_practice_dev_actions": dev_plan_details["strength_practice_dev_actions"],
      "weakness_practice_dev_actions": dev_plan_details["weakness_practice_dev_actions"],
      "recommended_category": dev_plan_details["mind_body_practice"].name,
      "chosen_personal_practices": dev_plan_details["mind_body_chosen_recommendations"],
      "sprint_number": current_sprint["sprint_number"]
    }

    # Import the render_template function from send_email.py
    from app.email.send_email import render_template
    
    # Render the email template with the same data
    rendered_html = render_template("initial-colleague-email.html", body)
    
    # Return the rendered HTML and email subject
    return {
      "html_content": rendered_html,
      "subject": f"Elevate - Colleague Invite for {user.first_name}'s Development Plan",
      "message": "Email preview generated successfully"
    }
      
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  

@router.post("/preview-initial-email-text")
async def preview_initial_email_text(db: db_dependency, data: DataFormSchema, token = Depends(verify_token)):
  """
  Preview the initial colleague email as structured text content.
  Returns the text content that would be sent to colleagues.
  """
  user_id = data.user_id

  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )

  try:
    # Get current dev plan
    dev_plan = await dev_plan_create_get_one(user_id=user_id, db=db)
    dev_plan_id=dev_plan["dev_plan_id"]
    current_sprint = await sprint_get_current(user_id=user_id, db=db, dev_plan_id=dev_plan_id)
    dev_plan_details = await get_review_details(user_id=user_id, sprint_number=current_sprint["sprint_number"], db=db)

    user = get_one_user_id(db=db, user_id=user_id)
    
    # Extract text content for preview
    strength_actions = []
    if dev_plan_details["strength_practice_dev_actions"]:
      for action in dev_plan_details["strength_practice_dev_actions"]:
        strength_actions.append(action.answer)
    
    weakness_actions = []
    if dev_plan_details["weakness_practice_dev_actions"]:
      for action in dev_plan_details["weakness_practice_dev_actions"]:
        weakness_actions.append(action.answer)
    
    # Return structured text data
    return {
      "subject": f"Leadership Development Plan - Would Love Your Thoughts",
      "user_name": user.first_name,
      "greeting": f"Hello,\n\nI'm engaging in a leadership development process and would love your input and support around the leadership development plan below.\n\nBest, {user.first_name}",
      "strength": dev_plan_details["chosen_strength"]["name"],
      "strength_practice": dev_plan_details["strength_practice"][0].name,
      "strength_actions": strength_actions,
      "weakness": dev_plan_details["chosen_weakness"]["name"],
      "weakness_practice": dev_plan_details["weakness_practice"][0].name,
      "weakness_actions": weakness_actions,
      "footer": "Peak Leadership Institute",
      "message": "Email text preview generated successfully"
    }
      
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))