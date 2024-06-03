import json
import numpy as np
from datetime import datetime, timezone
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.database.models import Users, Traits, Options
from app.utils.answers_crud import initial_questions_answers_all_forms_get_all

# def update_ave_std_traits() -> dict:
# # def update_trait_statistics(trait_data: dict, traits_from_database: List[Traits]) -> dict:     
#     # Open traits json file
#     with open("app/utils/data/traits.json", "r") as traits_json:
#         traits_data = json.load(traits_json)

#     # Get list of Trait objects from DB

#     # Convert the traits from the database into a dictionary for easier lookup
#     traits_dict = {trait.name: trait for trait in traits_data}
#     # Update the average and standard deviation for each trait in the JSON data
#     for i, trait_name in enumerate(trait_data["traits"]):
#         trait = traits_dict.get(trait_name)
#         if trait:
#             total_raw_score = trait.total_raw_score
#             if total_raw_score > 0:
#                 trait_data["traits_avg"][i] = total_raw_score / len(traits_from_database)
#             else:
#                 # If total_raw_score is 0, set average to 0
#                 trait_data["traits_avg"][i] = 0
            
#             # Calculate standard deviation using the updated average
#             if total_raw_score > 1:
#                 deviation_sum = sum((total_raw_score - trait.total_raw_score) ** 2 for trait in traits_from_database)
#                 variance = deviation_sum / len(traits_from_database)
#                 trait_data["traits_std"][i] = variance ** 0.5
#             else:
#                 # If total_raw_score is less than or equal to 1, set standard deviation to 0
#                 trait_data["traits_std"][i] = 0
#     return trait_data

async def update_ave_std(db: Session):
    latest_users = get_latest_users(db)

    with open("app/utils/data/traits.json", "r") as traits_json:
        traits_data = json.load(traits_json)
    trait_counts = {trait: 0 for trait in traits_data['traits']}
    
    for user in latest_users:
        initial_answers_form = await get_initial_question_answers(db, user.id)
        for form in initial_answers_form:
            for answer in form.answers: 
                option = db.query(Options).filter_by(id=answer.option_id).first()
                if option and option.trait_name:
                    trait_counts[option.trait_name] += 1
    
    traits_avgs = []
    traits_stds = []
    for trait in traits_data['traits']:
        avg, std = calculate_statistics(trait_counts[trait])
        traits_avgs.append(avg)
        traits_stds.append(std)
    
    update_traits_json(traits_data, traits_avgs, traits_stds)
    #update_traits_db(db, traits_avgs, traits_stds)

def calculate_statistics(trait_counts, old_avg):
    if trait_counts == 0:
        return None
    
    # average = ((oldAve*oldNumPoints) + x)/(oldNumPoints+1)
    std_dev = np.std(trait_counts)
    
    return average, std_dev

def update_traits_json(traits_data, new_avgs, new_stds):
    traits_data['traits_avg'] = new_avgs
    traits_data['traits_std'] = new_stds
    with open('traits.json', 'w') as file:
        json.dump(traits_data, file, indent=4)

def update_traits_db(db: Session, traits_avgs, traits_stds):
    with open("app/utils/data/traits.json", "r") as traits_json:
        traits_data = json.load(traits_json)

    for trait_name, avg, std in zip(traits_data['traits'], traits_avgs, traits_stds):
        traits = db.query(Traits).filter_by(name=trait_name).all()
        if traits:
            for trait in traits:
                trait.average = avg
                trait.standard_deviation = std
                db.flush()
    db.commit()

def check_user_count_divisible_by_ten(user_id: str, db: Session) -> bool:
    user_count = db.query(Users).count()
    current_user_date_created = db.query(Users.created_at).filter(
        Users.id == user_id
    ).first()

    if current_user_date_created:
        today = datetime.now(timezone.utc).date()
        if (current_user_date_created.date() == today) and (user_count % 10 == 0):
            return True
        
    return False

def get_latest_users(db: Session):
    return db.query(Users).order_by(desc(Users.created_at)).limit(10).all()

async def get_initial_question_answers(db: Session, user_id: str):
    return await initial_questions_answers_all_forms_get_all(db=db, user_id=user_id)


def increment_count(db: Session, endpoint_name: str) -> bool:
    input_count = db.query(EndpointCallCounter).filter_by(
        endpoint_name=endpoint_name
        ).first()
    
    if not input_count:
        input_count = EndpointCallCounter(
            endpoint_name=endpoint_name,
            count=1
        )
        db.add(input_count)
    else:
        input_count.count += 1
    db.commit()
    
    return input_count.count % 10 == 0