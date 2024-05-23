import time
from datetime import datetime, timezone
from app.email.send_email import send_email_background, send_email_async
from fastapi import BackgroundTasks
from sqlalchemy import cast, Date
from sqlalchemy.orm import Session
from app.database.models import UserColleagues
from app.utils.users_crud import get_one_user_id

async def send_week_5_9_emails(db: Session):
    print('---STARTED SEND WEEKS 5 AND 9 COLLEAGUE EMAILS FUNCTION---')
    today = datetime.now(timezone.utc).date()
    
    user_colleagues = db.query(UserColleagues).filter(
        (cast(UserColleagues.week_5_date, Date) == today) | (cast(UserColleagues.week_9_date, Date) == today)
    ).all()

    for colleague in user_colleagues:
        print(f'sent email to {colleague.email}')
        user = get_one_user_id(db=db, user_id=colleague.user_id)
        user_email_href = f"https://mail.google.com/mail/u/0/?view=cm&fs=1&tf=1&to={user.email}"
        
        subject = f"{user.first_name}'s Development Plan - Week 5" if colleague.week_5_date.date() == today else f"{user.first_name}'s Development Plan - Week 9"
        week_number = 5 if colleague.week_5_date.date() == today else 9
        body = {
            "colleague_email": colleague.email,
            "user_name": user.first_name,
            "user_email_href": user_email_href,
            "week_number": week_number
        }
        
        await send_email_async(
            body=body, 
            email_to=colleague.email, 
            subject=subject,
            template_name="sample-inline.html"
        )
    print('---FINISHED SEND WEEKS 5 AND 9 COLLEAGUE EMAILS FUNCTION---')
    
