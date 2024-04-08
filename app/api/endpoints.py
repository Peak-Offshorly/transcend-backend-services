from fastapi import APIRouter, HTTPException

from app.api.routes.account import router as account_router
from app.api.routes.traits import router as traits_router
from app.api.routes.traits_questions import router as traits_questions_router
from app.api.routes.account import router as account_router

router = APIRouter()
router.include_router(router=account_router)
router.include_router(router=traits_router)
router.include_router(router=traits_questions_router)
router.include_router(router=account_router)

@router.get("/")
async def health_check():
  try:
    return { "message": "Peak Test App is running" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
