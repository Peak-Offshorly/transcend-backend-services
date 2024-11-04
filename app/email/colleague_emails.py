import time
from datetime import datetime, timezone
from app.email.send_email import send_email_background, send_email_async
from fastapi import BackgroundTasks
from sqlalchemy import cast, Date
from sqlalchemy.orm import Session
from app.database.models import UserColleagues
from app.api.routes.development_plan import get_review_details
from app.utils.users_crud import get_one_user_id
from app.utils.dev_plan_crud import dev_plan_create_get_one
from app.utils.sprints_crud import sprint_get_current
from app.const import WEB_URL

async def user_colleague_week_5_9_emails(db: Session):
    print('---STARTED SEND WEEKS 5 AND 9 COLLEAGUE EMAILS FUNCTION---')
    today = datetime.now(timezone.utc).date()
    
    user_colleagues = db.query(UserColleagues).filter(
        (cast(UserColleagues.week_5_date, Date) == today) | (cast(UserColleagues.week_9_date, Date) == today)
    ).all()

    for colleague in user_colleagues:
        try:
            user = get_one_user_id(db=db, user_id=colleague.user_id)
            user_email_href = f"mailto:{user.email}"
            
            subject = f"Elevate - {user.first_name}'s Development Plan Week 5" if colleague.week_5_date.date() == today else f"Elevate - {user.first_name}'s Development Plan - Week 9"
            week_number = 5 if colleague.week_5_date.date() == today else 9
            colleague_email = colleague.email.split("@")

            # Get current dev plan
            dev_plan = await dev_plan_create_get_one(user_id=user.id, db=db)
            dev_plan_id=dev_plan["dev_plan_id"]
            current_sprint = await sprint_get_current(user_id=user.id, db=db, dev_plan_id=dev_plan_id)
            dev_plan_details = await get_review_details(user_id=user.id, sprint_number=current_sprint["sprint_number"], db=db)

            body = {
                "colleague_email": colleague_email[0],
                "user_name": user.first_name,
                "user_email_href": user_email_href,
                "week_number": week_number,
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
            
            await send_email_async(
                body=body, 
                email_to=colleague.email, 
                subject=subject,
                template_name="colleague-week-five-nine.html",
                reply_to=user.email,
                purpose="colleague_week_5_9"
            )
            print(f'Sent email to {colleague.email}')
        except Exception as e:
            print(f'Failed to send email to {colleague.email} due to {e}')

    print('---FINISHED SEND WEEKS 5 AND 9 COLLEAGUE EMAILS FUNCTION---')

async def user_colleague_week_12_emails(db: Session):
    print('---STARTED SEND WEEK 12 COLLEAGUE EMAILS FUNCTION---')
    today = datetime.now(timezone.utc).date()
    
    user_colleagues = db.query(UserColleagues).filter(
        (cast(UserColleagues.week_12_date, Date) == today)
    ).all()

    for colleague in user_colleagues:
        try:
            user = get_one_user_id(db=db, user_id=colleague.user_id)
            
            subject = f"Elevate - {user.first_name}'s Development Plan Colleague Survey"
            colleague_email = colleague.email.split("@")

            # Get current dev plan
            dev_plan = await dev_plan_create_get_one(user_id=user.id, db=db)
            dev_plan_id=dev_plan["dev_plan_id"]
            current_sprint = await sprint_get_current(user_id=user.id, db=db, dev_plan_id=dev_plan_id)
            dev_plan_details = await get_review_details(user_id=user.id, sprint_number=current_sprint["sprint_number"], db=db)

            body = {
                "colleague_email": colleague_email[0],
                "user_name": user.first_name,
                "survey_href": f"{WEB_URL}/survey/colleagues?token={colleague.survey_token}",
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
            
            await send_email_async(
                body=body, 
                email_to=colleague.email, 
                subject=subject,
                template_name="colleague-week-twelve-survey.html",
                reply_to=user.email,
                purpose="colleague_week_12"
            )
            print(f'Sent email to {colleague.email}')
        except Exception as e:
            print(f'Failed to send email to {colleague.email} due to {e}')
    
    print('---FINISHED SEND WEEK 12 COLLEAGUE EMAILS FUNCTION---')

#----FOR UAT OF JEREMY SETUP
async def user_colleague_week_12_emails_trigger(db: Session, user_id: str, background_tasks: BackgroundTasks):
    
    user_colleagues = db.query(UserColleagues).filter(
        UserColleagues.user_id == user_id
    ).all()
    statuses = []

    for colleague in user_colleagues:
        try:
            user = get_one_user_id(db=db, user_id=colleague.user_id)
            
            subject = f"Elevate - {user.first_name}'s Development Plan Colleague Survey"
            colleague_email = colleague.email.split("@")

            # Get current dev plan
            dev_plan = await dev_plan_create_get_one(user_id=user.id, db=db)
            dev_plan_id=dev_plan["dev_plan_id"]
            current_sprint = await sprint_get_current(user_id=user.id, db=db, dev_plan_id=dev_plan_id)
            dev_plan_details = await get_review_details(user_id=user.id, sprint_number=current_sprint["sprint_number"], db=db)

            body = {
                "colleague_email": colleague_email[0],
                "user_name": user.first_name,
                "survey_href": f"{WEB_URL}/survey/colleagues?token={colleague.survey_token}",
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
                body=body, 
                email_to=colleague.email, 
                subject=subject,
                template_name="colleague-week-twelve-survey.html",
                reply_to=user.email,
                background_tasks=background_tasks
            )
            statuses.append(f'Sent email to {colleague.email}')
        except Exception as e:
            statuses.append(f'Failed to send email to {colleague.email} due to {e}')

    return statuses
#----FOR UAT OF JEREMY SETUP
