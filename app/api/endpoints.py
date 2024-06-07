from fastapi import APIRouter, HTTPException

from app.api.routes.user import router as user_router
from app.api.routes.traits import router as traits_router
from app.api.routes.initial_questions import router as initial_questions_router
from app.api.routes.work_practices import router as work_practices
from app.api.routes.personal_practices import router as personal_practices
from app.api.routes.answers import router as answers
from app.api.routes.development_plan import router as development_plan
from app.api.routes.colleague_feedback import router as colleague_feedback
from app.api.routes.progress_check import router as progress_check
from app.api.routes.sprints import router as sprints
from app.api.routes.development_actions import router as development_actions

router = APIRouter()
router.include_router(router=user_router)
router.include_router(router=traits_router)
router.include_router(router=initial_questions_router)
router.include_router(router=work_practices)
router.include_router(router=personal_practices)
router.include_router(router=answers)
router.include_router(router=development_plan)
router.include_router(router=colleague_feedback)
router.include_router(router=progress_check)
router.include_router(router=sprints)
router.include_router(router=development_actions)

@router.get("/")
async def health_check():
  try:
    return { "message": "Peak Test App is running" }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
