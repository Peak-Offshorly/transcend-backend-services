import json
import math
from datetime import datetime, timezone
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from app.database.models import Users, Traits, Options, InitialAnswerTracker
from app.utils.answers_crud import initial_questions_answers_all_forms_get_all

async def update_ave_std(db: Session):
    print("---START UPDATE AVERAGE AND STANDARD DEVIATION OF COMPETENCIES FUNCTION---")

    latest_users = get_latest_users(db)
    additional_count = len(latest_users) # should be 10
    old_count = get_latest_count(db) - additional_count 

    with open("app/utils/data/traits.json", "r") as traits_json:
        traits_data = json.load(traits_json)
    trait_counts = {trait: 0 for trait in traits_data['traits']} # for average 
    trait_list_counts = {trait: [] for trait in traits_data['traits']} # for std
    
    for user in latest_users:
        initial_answers_form = await get_initial_question_answers(db, user.user_id)
        for form in initial_answers_form:
            user_trait_counts = {trait: 0 for trait in traits_data['traits']}
            for answer in form.answers: 
                option = db.query(Options).filter_by(id=answer.option_id).first()
                if option and option.trait_name:
                    trait_counts[option.trait_name] += 1
                    user_trait_counts[option.trait_name] += 1
            for trait, count in user_trait_counts.items():
                trait_list_counts[trait].append(count)
    
    traits_avgs = []
    traits_stds = []
    for i, trait in enumerate(traits_data['traits']):
        avg = calculate_average(
            trait_counts=trait_counts[trait],
            old_avg=traits_data['traits_avg'][i],
            old_count=old_count,
            additional_count=additional_count
        )
        traits_avgs.append(avg)
        
    
    for i, trait in enumerate(traits_data['traits']):
        std = calculate_std(
            trait_list_counts=trait_list_counts[trait],
            old_avg=traits_data['traits_avg'][i],
            old_std=traits_data['traits_std'][i],
            new_avg=traits_avgs[i],
            old_count=old_count,
            additional_count=additional_count
        )
        traits_stds.append(std)

    update_traits_json(traits_data, traits_avgs, traits_stds)
    print("-updated JSON Traits data")
    
    update_traits_db(db, traits_avgs, traits_stds)
    print("-updated database Traits data")

    print("---FINISH UPDATE AVERAGE AND STANDARD DEVIATION OF COMPETENCIES FUNCTION---")

def calculate_average(trait_counts, old_avg, old_count, additional_count):
    # update average formula = ((oldAve*oldCount) + sumOfNewDataPoints)/(oldNumPoints+newCount)
    new_average = ((old_avg * old_count) + trait_counts) / float(old_count + additional_count)
    
    return new_average

def calculate_std(trait_list_counts, old_count, additional_count, old_avg, new_avg, old_std):
    sum_of_squared_deviations = old_std ** 2 * (old_count - 1)
    for element in trait_list_counts:
        deviation = element - new_avg
        sum_of_squared_deviations += deviation ** 2

    new_std = math.sqrt(sum_of_squared_deviations / ((old_count + additional_count) - 1))

    return new_std

def update_traits_json(traits_data, new_avgs, new_stds):
    traits_data['traits_avg'] = new_avgs
    traits_data['traits_std'] = new_stds
    with open("app/utils/data/traits.json", 'w') as file:
        json.dump(traits_data, file, indent=3)

def update_traits_db(db: Session, traits_avgs, traits_stds):
    with open("app/utils/data/traits.json", "r") as traits_json:
        traits_data = json.load(traits_json)

    for trait_name, avg, std in zip(traits_data['traits'], traits_avgs, traits_stds):
        traits = db.query(Traits).filter_by(name=trait_name, user_id='rYtdeQbtD1N71PCpmkvAyZQGN442').all()
        if traits:
            for trait in traits:
                trait.average = avg
                trait.standard_deviation = std
                db.flush()
    db.commit()

def increment_count(db: Session, user_id: str) -> bool:
    initial_answer_inputs = db.query(InitialAnswerTracker).all()

    if len(initial_answer_inputs) == 0:
        new_initial_answer_input = InitialAnswerTracker(
            user_id=user_id,
            count=102 # 101 is the original count of inputs, new input would be 102
        )
        db.add(new_initial_answer_input)
        db.commit()
    else:
        latest_count = get_latest_count(db=db)
        additional_initial_answer_input = InitialAnswerTracker(
            user_id=user_id,
            count=latest_count + 1
        )
        db.add(additional_initial_answer_input)
        db.commit()

    # if 10 additional inputs, return True 
    input_count = db.query(InitialAnswerTracker).count()
    if input_count % 10 == 0:
        return True
    
    return False

def get_latest_users(db: Session):
    return db.query(InitialAnswerTracker).order_by(desc(InitialAnswerTracker.created_at)).limit(10).all()

def get_latest_count(db: Session):
    return db.query(func.max(InitialAnswerTracker.count)).scalar()

async def get_initial_question_answers(db: Session, user_id: str):
    return await initial_questions_answers_all_forms_get_all(db=db, user_id=user_id)

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