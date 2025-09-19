from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database.models import PendingActions

# Creates one pending action
async def pending_actions_create_one(db: Session, user_id: str, action: str, category: str):
    new_pending_action = PendingActions(
        user_id=user_id,
        action=action,
        category=category
    )
    
    db.add(new_pending_action)
    db.commit()

# Bulk create for better performance
async def pending_actions_create_bulk(db: Session, user_id: str, actions: list, category: str):
    pending_actions = [
        PendingActions(
            user_id=user_id,
            action=action,
            category=category
        )
        for action in actions
    ]
    
    db.add_all(pending_actions)
    db.commit()

# Returns all pending actions under a user_id and category
async def pending_actions_read(db: Session, user_id: str, category: str):
    pending_actions = db.query(PendingActions).filter(
        PendingActions.user_id == user_id,
        PendingActions.category == category
    ).all()

    if pending_actions:
        return pending_actions
    
    return None

# Clears all pending actions under a user_id
async def pending_actions_clear_all(db: Session, user_id: str):
    # bulk delete for better performance
    db.query(PendingActions).filter(
        PendingActions.user_id == user_id
    ).delete()
    
    db.commit()
