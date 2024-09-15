from app.models import db
from datetime import datetime, timezone

class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sent_to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=False)

    def __repr__(self):
        return f'<Email {self.id} for case {self.case_id}>'