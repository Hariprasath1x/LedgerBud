from datetime import datetime
from app.extensions import db


class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchants.id'), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    frequency = db.Column(db.String(30), nullable=False, default='monthly')  # monthly, weekly, yearly, quarterly
    last_detected = db.Column(db.Date, nullable=True)
    next_expected = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    merchant = db.relationship('Merchant', back_populates='subscriptions')

    def to_dict(self):
        return {
            'id': self.id,
            'merchant_id': self.merchant_id,
            'merchant_name': self.merchant.canonical_name if self.merchant else self.name,
            'name': self.name,
            'amount': float(self.amount),
            'frequency': self.frequency,
            'last_detected': self.last_detected.isoformat() if self.last_detected else None,
            'next_expected': self.next_expected.isoformat() if self.next_expected else None,
            'is_active': self.is_active,
        }

    def __repr__(self):
        return f'<Subscription {self.name} {self.amount}/{self.frequency}>'


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)  # e.g. STATEMENT_UPLOADED, TRANSACTIONS_IMPORTED
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    import_job_id = db.Column(db.Integer, db.ForeignKey('import_jobs.id'), nullable=True)
    meta_data = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    import_job = db.relationship('ImportJob', back_populates='audit_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'import_job_id': self.import_job_id,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<AuditLog {self.action} at {self.created_at}>'
