from app.models import db
from datetime import datetime, timezone

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    address = db.Column(db.String(200))
    address_status = db.Column(db.String(50), default='valid')
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)

    cases_as_debtor = db.relationship('Case', foreign_keys='Case.debtor_id', backref='debtor', lazy='dynamic')
    cases_as_creditor = db.relationship('Case', foreign_keys='Case.creditor_id', backref='creditor', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.id}: {self.name}>'