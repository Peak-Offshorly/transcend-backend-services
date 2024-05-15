from app import create_app
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from httpx import AsyncClient
import uvicorn
import os
import fastapi

load_dotenv()
print("Started App:", os.environ.get("APP_NAME", "Peak Test App"))

app: fastapi.FastAPI = create_app()

async def check_user_activity():
    async with AsyncClient(app=app, base_url="http://0.0.0.0:10000") as client:
        await client.get("/accounts/check-if-active")

# Create an instance of the scheduler
scheduler = AsyncIOScheduler()
# Schedule to run every 3 weeks
scheduler.add_job(check_user_activity, "interval", weeks=3)
# Start the scheduler
scheduler.start()
print("Started CRON scheduler")

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

  
