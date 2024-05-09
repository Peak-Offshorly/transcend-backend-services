from fastapi import APIRouter, HTTPException

from app.api.routes.user import router as user_router
from app.api.routes.traits import router as traits_router
from app.api.routes.initial_questions import router as initial_questions_router
from app.api.routes.work_practices import router as work_practices
from app.api.routes.personal_practices import router as personal_practices
from app.api.routes.answers import router as answers

router = APIRouter()
router.include_router(router=user_router)
router.include_router(router=traits_router)
router.include_router(router=initial_questions_router)
router.include_router(router=work_practices)
router.include_router(router=personal_practices)
router.include_router(router=answers)

@router.get("/")
async def health_check():
  try:
    return { "message": "Peak Test App is running" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
