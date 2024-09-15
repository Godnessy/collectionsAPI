from app.models import db

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    users = db.relationship('User', backref='company', lazy='dynamic')

    def __repr__(self):
        return f'<Company {self.id}: {self.name}>'