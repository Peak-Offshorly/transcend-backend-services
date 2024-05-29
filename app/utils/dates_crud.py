from uuid import UUID
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database.models import ChosenTraits, PersonalPracticeCategory, Sprints, DevelopmentPlan

async def add_dates(chosen_traits_data, recommended_mind_body_category_data, chosen_trait_practices, dev_plan, db: Session):
    # Add dates for chosen_traits(strength/weakness) and mind body area
    # Both span 12 weeks 

    # Get the current date and end date which is 12 weeks from the start date
    start_date = datetime.now(tz=timezone.utc)
    end_date = start_date + timedelta(weeks=12)

    # Add dates to chosen_traits(strength/weakness), mind body area and dev plan
    chosen_strength = db.query(ChosenTraits).filter(
        ChosenTraits.user_id == chosen_traits_data["user_id"],
        ChosenTraits.name == chosen_traits_data["chosen_strength"]["name"],
        ChosenTraits.trait_type == "STRENGTH",
        ChosenTraits.development_plan_id == dev_plan["dev_plan_id"]
    ).first()
    chosen_strength.start_date = start_date
    chosen_strength.end_date = end_date
    
    chosen_weakness = db.query(ChosenTraits).filter(
        ChosenTraits.user_id == chosen_traits_data["user_id"],
        ChosenTraits.name == chosen_traits_data["chosen_weakness"]["name"],
        ChosenTraits.trait_type == "WEAKNESS",
        ChosenTraits.development_plan_id == dev_plan["dev_plan_id"]
    ).first()
    chosen_weakness.start_date = start_date
    chosen_weakness.end_date = end_date

    mind_body_area = db.query(PersonalPracticeCategory).filter(
        PersonalPracticeCategory.id == recommended_mind_body_category_data.id,
        PersonalPracticeCategory.development_plan_id == dev_plan["dev_plan_id"]
    ).first()
    mind_body_area.start_date = start_date
    mind_body_area.end_date = end_date

    current_dev_plan = db.query(DevelopmentPlan).filter(
        DevelopmentPlan.id == dev_plan["dev_plan_id"]
    ).first()
    current_dev_plan.start_date = start_date
    current_dev_plan.end_date = end_date

    # Add start_date and start_to_mid_date for Sprint 1
    start_to_mid_date = start_date + timedelta(weeks=6)
    sprint1 = db.query(Sprints).filter(
        Sprints.id == chosen_trait_practices["chosen_strength_practice"][0].sprint_id,
        Sprints.development_plan_id == dev_plan["dev_plan_id"]
    ).first()
    sprint1.start_date = start_date
    sprint1.end_date = start_to_mid_date

    db.commit()

async def compute_second_sprint_dates(start_to_mid_date: datetime, end_date: datetime):
    sprint_2_start_date = start_to_mid_date + timedelta(seconds=1)
    sprint_2_end_date = end_date
    
    return {
        "start_date": sprint_2_start_date,
        "end_date": sprint_2_end_date
    } 

# Returns the start and end dates for colleague messages
async def compute_colleague_message_dates(start_date: datetime, end_date: datetime): 
    # Initialize a list to store start and end dates for each week
    weekly_dates = []

    # Iterate over the 12-week period
    for week_number in range(1, 13):
        # Calculate the start date for the current week
        week_start_date = start_date + timedelta(weeks=week_number - 1)

        # Calculate the end date for the current week
        week_end_date = week_start_date + timedelta(days=7)

        # Ensure the end date does not exceed the overall end date
        if week_end_date > end_date:
            week_end_date = end_date

        # Append the start and end dates to the list
        weekly_dates.append((week_start_date, week_end_date))

    return {
        "week_1": weekly_dates[0],
        "week_5": weekly_dates[4],
        "week_9": weekly_dates[8],
        "week_12": weekly_dates[11],
    }

