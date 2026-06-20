from datetime import datetime
from app.extensions import db


class Wallet(db.Model):
    __tablename__ = 'wallets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False, default='bank')  # bank, credit_card, cash, digital
    balance = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    currency = db.Column(db.String(10), default='INR')
    institution = db.Column(db.String(100), nullable=True)
    account_number = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(20), default='#6c63ff')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transactions = db.relationship('Transaction', back_populates='wallet', lazy='dynamic')
    import_jobs = db.relationship('ImportJob', back_populates='wallet', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'balance': float(self.balance),
            'currency': self.currency,
            'institution': self.institution,
            'account_number': self.account_number,
            'color': self.color,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Wallet {self.name}>'
