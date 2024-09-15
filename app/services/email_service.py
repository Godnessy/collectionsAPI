from app.models import db, Email
from datetime import datetime, timezone

def create_email_notification(user_id, case_id, message):
    new_email = Email(
        created_at=datetime.now(timezone.utc),
        message=message,
        sent_to_user_id=user_id,
        case_id=case_id
    )
    db.session.add(new_email)
    db.session.commit()
    # In a real application, you would send the actual email here
    print(f"Email notification created for user {user_id}, case {case_id}")