from app import create_app
from dotenv import load_dotenv
import uvicorn
import os
import fastapi

load_dotenv()
print("Started App:", os.environ.get("APP_NAME", "Peak Test App"))

app: fastapi.FastAPI = create_app()


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
