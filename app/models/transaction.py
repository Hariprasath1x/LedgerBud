from datetime import datetime
from app.extensions import db


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchants.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    import_job_id = db.Column(db.Integer, db.ForeignKey('import_jobs.id'), nullable=True)

    # Transaction data
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=False)
    merchant_name_raw = db.Column(db.String(500), nullable=True)  # Raw from statement
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    type = db.Column(db.String(10), nullable=False, default='debit')  # debit / credit
    balance_after = db.Column(db.Numeric(15, 2), nullable=True)
    reference_no = db.Column(db.String(200), nullable=True)

    # Processing flags
    is_duplicate = db.Column(db.Boolean, default=False)
    is_manual = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    wallet = db.relationship('Wallet', back_populates='transactions')
    merchant = db.relationship('Merchant', back_populates='transactions')
    category = db.relationship('Category', back_populates='transactions')
    import_job = db.relationship('ImportJob', back_populates='transactions')

    def to_dict(self):
        return {
            'id': self.id,
            'wallet_id': self.wallet_id,
            'wallet_name': self.wallet.name if self.wallet else None,
            'merchant_id': self.merchant_id,
            'merchant_name': self.merchant.canonical_name if self.merchant else self.merchant_name_raw,
            'category_id': self.category_id,
            'category': self.category.to_dict() if self.category else None,
            'date': self.date.isoformat() if self.date else None,
            'description': self.description,
            'amount': float(self.amount),
            'type': self.type,
            'balance_after': float(self.balance_after) if self.balance_after else None,
            'reference_no': self.reference_no,
            'is_duplicate': self.is_duplicate,
            'is_manual': self.is_manual,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Transaction {self.id} {self.type} {self.amount}>'
