import time
from datetime import datetime, timezone, timedelta
from app.email.send_email import send_email_background, send_email_async
from fastapi import BackgroundTasks
from sqlalchemy import cast, Date
from sqlalchemy.orm import Session
from app.database.models import DevelopmentPlan
from app.api.routes.development_plan import get_review_details
from app.utils.users_crud import get_one_user_id
from app.utils.dev_plan_crud import dev_plan_create_get_one
from app.utils.sprints_crud import sprint_get_current
from app.const import WEB_URL

async def user_weekly_email(db: Session):
    print('---STARTED SEND USER WEEKLY EMAILS FUNCTION---')
    
    today = datetime.now(timezone.utc).date()
    
    # Query all active development plans
    active_plans = db.query(DevelopmentPlan).filter(
        DevelopmentPlan.is_finished == False,
        cast(DevelopmentPlan.start_date, Date) <= today,
        cast(DevelopmentPlan.end_date, Date) >= today
    ).all()

    for plan in active_plans:
        try:
            # Get current week number
            start_date = plan.start_date.date()
            week_number = ((today - start_date).days // 7) + 1

            # Calculate the end date of the current week
            current_week_end_date = start_date + timedelta(days=(week_number * 7))

            if week_number > 0 and week_number <= 12 and today == current_week_end_date:
                user = get_one_user_id(user_id=plan.user_id, db=db)

                # Get current dev plan
                dev_plan = await dev_plan_create_get_one(user_id=user.id, db=db)
                dev_plan_id = dev_plan["dev_plan_id"]
                current_sprint = await sprint_get_current(user_id=user.id, db=db, dev_plan_id=dev_plan_id)
                dev_plan_details = await get_review_details(user_id=user.id, sprint_number=current_sprint["sprint_number"], db=db)

                # Sprint first or second variable
                sprint_first_second = "first" if current_sprint["sprint_number"] == 1 else "second"
                
                # Prep email body and send email to user
                subject = f"Elevate - Development Plan Progress Check for Week {week_number}"
                body = {
                    "user_name": user.first_name,
                    "progress_check_link": f"{WEB_URL}/progress-check",
                    "week_number": week_number,
                    "strength": dev_plan_details["chosen_strength"]["name"],
                    "weakness": dev_plan_details["chosen_weakness"]["name"],
                    "strength_practice": dev_plan_details["strength_practice"][0].name if dev_plan_details["strength_practice"] else None,
                    "weakness_practice": dev_plan_details["weakness_practice"][0].name if dev_plan_details["weakness_practice"] else None,
                    "strength_practice_dev_actions": dev_plan_details["strength_practice_dev_actions"],
                    "weakness_practice_dev_actions": dev_plan_details["weakness_practice_dev_actions"],
                    "recommended_category": dev_plan_details["mind_body_practice"].name,
                    "chosen_personal_practices": dev_plan_details["mind_body_chosen_recommendations"],
                    "sprint_number": current_sprint["sprint_number"],
                    "sprint_first_second": sprint_first_second
                }

                await send_email_async(
                    body=body, 
                    email_to=user.email,
                    subject=subject,
                    template_name="user-weekly-email.html",
                    reply_to=user.email,
                    purpose="user_weekly_email"
                )
                print(f'Sent email to {user.email}')
        except Exception as e:
                print(f'Failed to send email to user {plan.user_id} due to {e}')

    print('---FINISHED SEND USER WEEKLY EMAILS FUNCTION---')
    
