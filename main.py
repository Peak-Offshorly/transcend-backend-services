import uvicorn
import os
import fastapi
from app import create_app
from dotenv import load_dotenv
from fastapi import BackgroundTasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from httpx import AsyncClient
from datetime import timezone
from app.database.connection import get_db
from app.email.colleague_emails import send_week_5_9_emails

load_dotenv()
print("Started App:", os.environ.get("APP_NAME", "Peak Test App"))

app: fastapi.FastAPI = create_app()

#----CRON JOBS
async def check_user_activity():
    async with AsyncClient(app=app, base_url="http://0.0.0.0:10000") as client:
        await client.get("/accounts/check-if-active")

async def send_weekly_emails_job():
    db = next(get_db())
    background_tasks = BackgroundTasks()
    await send_week_5_9_emails(db=db, background_tasks=background_tasks)

scheduler = AsyncIOScheduler()
# Run check_user_activity every 3 weeks
scheduler.add_job(check_user_activity, "interval", weeks=3)
# Run the send_weekly_emails job to run daily
scheduler.add_job(send_weekly_emails_job, "cron", hour=23, minute=50, timezone=timezone.utc)

scheduler.start()
print("Started CRON jobs")
#-------------

if __name__ == "__main__":
  uvicorn.run(
    app="main:app",
    
    # Server Host and Port used for Render 
    # host=os.environ.get("SERVER_HOST", "0.0.0.0"),
    # port=os.environ.get("SERVER_PORT", 10000),

    host=os.environ.get("SERVER_HOST", "127.0.0.1"),
    port=os.environ.get("SERVER_PORT", 9001),
    log_level="info",
    reload=True,
  )

  
