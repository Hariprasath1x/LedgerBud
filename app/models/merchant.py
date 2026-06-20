from datetime import datetime
from app.extensions import db


class Merchant(db.Model):
    __tablename__ = 'merchants'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    canonical_name = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    keywords = db.Column(db.JSON, default=list)  # List of keyword strings for fuzzy matching
    logo_url = db.Column(db.String(500), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    category = db.relationship('Category', back_populates='merchants')
    transactions = db.relationship('Transaction', back_populates='merchant', lazy='dynamic')
    subscriptions = db.relationship('Subscription', back_populates='merchant', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'canonical_name': self.canonical_name,
            'category_id': self.category_id,
            'category': self.category.to_dict() if self.category else None,
            'keywords': self.keywords or [],
            'is_verified': self.is_verified,
        }

    def __repr__(self):
        return f'<Merchant {self.canonical_name}>'
