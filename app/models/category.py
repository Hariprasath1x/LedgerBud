from datetime import datetime
from app.extensions import db


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    type = db.Column(db.String(20), nullable=False, default='expense')  # income / expense
    color = db.Column(db.String(20), default='#6c63ff')
    icon = db.Column(db.String(50), default='tag')
    is_system = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    merchants = db.relationship('Merchant', back_populates='category', lazy='dynamic')
    transactions = db.relationship('Transaction', back_populates='category', lazy='dynamic')
    budgets = db.relationship('Budget', back_populates='category', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'color': self.color,
            'icon': self.icon,
            'is_system': self.is_system,
        }

    def __repr__(self):
        return f'<Category {self.name}>'
