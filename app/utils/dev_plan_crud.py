from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database.models import DevelopmentPlan

async def dev_plan_create_one(chosen_traits_data, recommended_mind_body_category_data, chosen_trait_practices, user_id: str, db: Session):
    max_dev_plan_number = db.query(func.max(DevelopmentPlan.number)).filter(
        DevelopmentPlan.user_id == user_id
    ).scalar()

    if max_dev_plan_number is None:
        first_dev_plan = DevelopmentPlan(
            user_id=user_id,
            number=1,
            chosen_strength_id=chosen_traits_data["chosen_strength"]["id"],
            chosen_weakness_id=chosen_traits_data["chosen_weakness"]["id"]
        )