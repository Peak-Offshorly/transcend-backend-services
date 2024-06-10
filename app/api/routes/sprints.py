from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from app.schemas.models import DataFormSchema
from app.database.connection import get_db
from app.firebase.utils import verify_token
from app.utils.dev_plan_crud import dev_plan_create_get_one
from app.utils.sprints_crud import sprint_get_current, sprint_update_is_finished_true

db_dependency = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/sprints", tags=["sprints"])

@router.get("/current-sprint")
async def get_current_sprint(user_id: str, db: db_dependency, token = Depends(verify_token)):
  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )

  try:
    dev_plan = await dev_plan_create_get_one(db=db, user_id=user_id)
    return await sprint_get_current(db=db, user_id=user_id, dev_plan_id=dev_plan["dev_plan_id"])
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  

# Finish first/second sprint
@router.post("/finish-sprint")
async def finish_sprint(data: DataFormSchema, db: db_dependency, token = Depends(verify_token)):
  user_id = data.user_id
  if token != user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this action."
    )


  try:
    dev_plan = await dev_plan_create_get_one(db=db, user_id=user_id)
    dev_plan_id = dev_plan["dev_plan_id"]
    sprint = await sprint_get_current(db=db, user_id=user_id, dev_plan_id=dev_plan_id)
    sprint_id = sprint["sprint_id"]
    sprint_number = sprint["sprint_number"]
    
    if sprint_id is None:
      return { "message": f"No sprint id for sprint number {sprint_number}" }
    
    response = await sprint_update_is_finished_true(db=db, user_id=user_id, dev_plan_id=dev_plan_id, sprint_id=sprint_id)

    return { "message": response["message"] }
  except Exception as error:
    raise HTTPException(status_code=400, detail=str(error))
  