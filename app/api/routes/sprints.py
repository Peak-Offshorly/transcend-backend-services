from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.connection import get_db
from app.utils.dev_plan_crud import dev_plan_create_get_one
from app.utils.sprints_crud import sprint_get_current

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/sprints", tags=["sprints"])

@router.get("/current-sprint")
async def get_current_sprint(user_id: str, db: db_dependency):
  try:
    dev_plan = await dev_plan_create_get_one(db=db, user_id=user_id)
    return await sprint_get_current(db=db, user_id=user_id, dev_plan_id=dev_plan["dev_plan_id"])
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))