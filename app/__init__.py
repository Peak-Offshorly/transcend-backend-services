from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router

def create_app() -> FastAPI:
    app = FastAPI()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
        "http://localhost:5173",  
        "http://localhost:5174",  
        "https://peak-transcend-dev.netlify.app",
        "https://admin-transcend-dev.netlify.app",
        "https://peak-transcend-staging.netlify.app"

        # make sure to add the frontend url here for dev and staging 
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(router=router)

    return app