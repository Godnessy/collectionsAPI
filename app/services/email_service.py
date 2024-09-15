from app.models import db, Email
from datetime import datetime, timezone

def create_email_notification(user_id, case_id):
    new_email = Email(
        created_at=datetime.now(timezone.utc),
        case_id=case_id,
        sent_to_user_id=user_id,
        message='Debtor Address is invalid'
    )

    print(new_email.message)
    db.session.add(new_email)
    db.session.commit()


def send_email(email):
    #mock sending email
    print('sent email to user regarding change of case status')
    return 