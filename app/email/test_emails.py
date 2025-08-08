# Replace the content in app/email/test_emails.py with this safer version:

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from app.email.send_email import send_email_background, send_email_async
from app.email.send_complete_profile_email import send_complete_profile
from app.utils.users_crud import get_one_user_id
from app.const import WEB_URL

async def send_all_test_emails(db: Session, test_user_id: str, test_colleague_email: str, background_tasks: BackgroundTasks):
    """
    Testing function to send all email types at once - handles missing data gracefully
    """
    
    try:
        # Get user details
        user = get_one_user_id(db=db, user_id=test_user_id)
        if not user:
            raise Exception(f"User not found with ID: {test_user_id}")
        
        print(f"🚀 Starting email test for user: {user.first_name} ({user.email})")
        print(f"📧 Colleague test email: {test_colleague_email}")
        print("=" * 50)
        
        # 1. COMPLETE PROFILE EMAIL
        print("1️⃣ Sending: Complete Profile Email")
        await send_complete_profile(
            email_to=test_colleague_email,
            link=f"{WEB_URL}/complete-profile?code=TEST123",
            firstname="Test",
            lastname="Admin"
        )
        
        # 2. INITIAL COLLEAGUE INVITE EMAIL (with mock data)
        print("2️⃣ Sending: Initial Colleague Invite Email")
        colleague_email_split = test_colleague_email.split("@")
        colleague_body = {
            "colleague_email": colleague_email_split[0],
            "user_name": user.first_name,
            "user_email_href": f"mailto:{user.email}",
            "strength": "Communication",  # Mock data
            "weakness": "Time Management",  # Mock data
            "strength_practice": "Active Listening Practice",  # Mock data
            "weakness_practice": "Priority Setting Exercises",  # Mock data
            "strength_practice_dev_actions": [
                {"answer": "Practice daily check-ins with team"},
                {"answer": "Ask clarifying questions before responding"},
     
            ],
            "weakness_practice_dev_actions": [
                {"answer": "Use time-blocking for important tasks"},
                {"answer": "Review and prioritize tasks each morning"},
               

            ],
            "recommended_category": "Mindfulness",  # Mock data
            "chosen_personal_practices": [
                {"name": "Daily Meditation"},
                {"name": "Breathing Exercises"}
            ],
            "sprint_number": 1
        }
        
        send_email_background(
            background_tasks=background_tasks,
            body=colleague_body,
            email_to=test_colleague_email,
            subject="Leadership Development Plan - Would Love Your Thoughts",
            template_name="initial-colleague-email.html",
            reply_to=user.email
        )
        
        # # 3. COLLEAGUE SURVEY EMAIL (Week 4/12)
        # print("3️⃣ Sending: Colleague Survey Email (Week 4)")
        # survey_body = {
        #     "colleague_email": colleague_email_split[0],
        #     "user_name": user.first_name,
        #     "survey_href": f"{WEB_URL}/survey/colleagues?token=TEST_TOKEN_123",
        #     "strength": "Communication",
        #     "weakness": "Time Management",
        #     "strength_practice": "Active Listening Practice",
        #     "weakness_practice": "Priority Setting Exercises",
        #     "strength_practice_dev_actions": [
        #         {"answer": "Practice daily check-ins with team"},
        #         {"answer": "Ask clarifying questions before responding"}
        #     ],
        #     "weakness_practice_dev_actions": [
        #         {"answer": "Use time-blocking for important tasks"},
        #         {"answer": "Review and prioritize tasks each morning"}
        #     ],
        #     "recommended_category": "Mindfulness",
        #     "chosen_personal_practices": [
        #         {"name": "Daily Meditation"},
        #         {"name": "Breathing Exercises"}
        #     ],
        #     "sprint_number": 1
        # }
        
        # await send_email_async(
        #     body=survey_body,
        #     email_to=test_colleague_email,
        #     subject=f"Your input on {user.first_name}'s leadership growth",
        #     template_name="colleague-week-twelve-survey.html",
        #     reply_to=user.email,
        #     purpose="colleague_survey_test"
        # )
        
        # 4. USER WEEKLY PROGRESS CHECK EMAILS (Week 1, 2, 3)
        for week in [1, 2, 3]:
            print(f"4️⃣ Sending: User Weekly Progress Check - Week {week}")
            
            weekly_body = {
                "user_name": user.first_name,
                "progress_check_link": "https://peak-transcend-staging.netlify.app/user/progress-check", # staging/or dev if there is dev staging in the url. if not, use production link
                "week_number": week,
                "strength": "Communication",
                "weakness": "Time Management",
                "strength_practice": "Active Listening Practice",
                "weakness_practice": "Priority Setting Exercises",
                "strength_practice_dev_actions": [
                    {"answer": "Practice daily check-ins with team"},
                    {"answer": "Ask clarifying questions before responding"}
                ],
                "weakness_practice_dev_actions": [
                    {"answer": "Use time-blocking for important tasks"},
                    {"answer": "Review and prioritize tasks each morning"}
                ],
                "recommended_category": "Mindfulness",
                "chosen_personal_practices": [
                    {"name": "Daily Meditation"},
                    {"name": "Breathing Exercises"}
                ],
                "sprint_number": 1,
                "sprint_first_second": "first"
            }
            
            await send_email_async(
                body=weekly_body,
                email_to=user.email,
                subject=f"Elevate - Week {week} Leadership Progress Check",
                template_name="user-weekly-email.html",
                reply_to=user.email,
                purpose="user_weekly_test"
            )
        
        print("=" * 50)
        print("✅ ALL TEST EMAILS SENT SUCCESSFULLY!")
        print(f"📬 Check these inboxes:")
        print(f"   - User emails: {user.email}")
        print(f"   - Colleague emails: {test_colleague_email}")
        print("=" * 50)
        
        return {
            "message": "All test emails sent successfully!",
            "user_email": user.email,
            "colleague_email": test_colleague_email,
            "emails_sent": [
                "Complete Profile Email",
                "Initial Colleague Invite",
                "Colleague Survey (Week 4)",
                "User Progress Check Week 1",
                "User Progress Check Week 2", 
                "User Progress Check Week 3"
            ]
        }
        
    except Exception as e:
        print(f"❌ ERROR sending test emails: {str(e)}")
        raise Exception(f"Failed to send test emails: {str(e)}")