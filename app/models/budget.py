from datetime import datetime
from app.extensions import db


class Budget(db.Model):
    __tablename__ = 'budgets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    period = db.Column(db.String(20), nullable=False, default='monthly')  # monthly, weekly, yearly
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    category = db.relationship('Category', back_populates='budgets')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category_id': self.category_id,
            'category': self.category.to_dict() if self.category else None,
            'amount': float(self.amount),
            'period': self.period,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active,
        }

    def __repr__(self):
        return f'<Budget {self.name} {self.amount}>'
