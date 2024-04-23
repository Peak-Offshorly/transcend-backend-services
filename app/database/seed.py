import uuid
from random import choice, randint
from sqlalchemy.orm import Session
from app.database.models import Users, Sprints, Forms, Questions, Traits, Options, UserTraits, Practices, DevelopmentPlan, UserDevelopmentPlan
from app.database.connection import get_db

def seed_test_data(db: Session):
    # Seed Users
    users = []
    for _ in range(5):
        user_id = str(uuid.uuid4())
        users.append(Users(
            id=user_id,
            email=f"user{user_id[:8]}@example.com",
            first_name=f"First{user_id[:4]}",
            last_name=f"Last{user_id[4:8]}",
            role=choice(["admin", "user"])
        ))
    db.add_all(users)
    db.commit()

    # Seed Sprints
    sprints = []
    for sprint_id in range(1, 3):
        sprints.append(Sprints(id=uuid.uuid4(), name=sprint_id))
    db.add_all(sprints)
    db.commit()


    # Seed DevelopmentPlan and UserDevelopmentPlan
    development_plans = []
    user_development_plans = []
    for user in users:
        development_plan_id = uuid.uuid4()
        development_plans.append(DevelopmentPlan(
            id=development_plan_id,
            name=f"Development Plan for {user.first_name} {user.last_name}"
        ))
        user_development_plans.append(UserDevelopmentPlan(
            id=uuid.uuid4(),
            user_id=user.id,
            development_plan_id=development_plan_id
        ))
    db.add_all(development_plans)
    db.add_all(user_development_plans)
    db.commit()

# Get a database session
db_session: Session = get_db()

# Call the seed_test_data function to populate the database with test data
print("i ran here")
seed_test_data(db_session)

# Commit the changes to the database
db_session.commit()

# Close the database session
db_session.close()
