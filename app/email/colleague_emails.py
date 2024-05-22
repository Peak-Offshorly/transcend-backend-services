from datetime import datetime, timezone
from app.email.send_email import send_email_background
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from app.database.models import UserColleagues
from app.utils.users_crud import get_one_user_id

async def send_week_5_9_emails(db: Session, background_tasks: BackgroundTasks):
    print('started send_week_5_9_emails function')
    today = datetime.now(timezone.utc).date()

    user_colleagues = db.query(UserColleagues).filter(
        (UserColleagues.week_5_date == today) | (UserColleagues.week_9_date == today)
    ).all()

    for colleague in user_colleagues:
        print(f'sent email to {colleague.email}')
        user = get_one_user_id(db=db, user_id=colleague.user_id)
        user_email_href = f"https://mail.google.com/mail/u/0/?view=cm&fs=1&tf=1&to={user.email}"
        
        body = {
            "colleague_email": colleague.email,
            "user_name": user.first_name,
            "user_email_href": user_email_href
        }

        subject = f"{user.first_name}'s Development Plan - Week 5" if colleague.week_5_date == today else f"{user.first_name}'s Development Plan - Week 9"

        send_email_background(
            background_tasks=background_tasks, 
            body=body, 
            email_to=colleague.email, 
            subject=subject,
            template_name="sample-inline.html"
        )
