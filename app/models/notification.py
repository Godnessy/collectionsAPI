from app.models import db
from datetime import datetime, timezone

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=False)
    address_status = db.Column(db.String(50), nullable=False)
    reason = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Notification {self.id} for case {self.case_id}>'