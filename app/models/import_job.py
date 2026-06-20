from datetime import datetime
from app.extensions import db


class ImportJob(db.Model):
    __tablename__ = 'import_jobs'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # pdf, csv, xlsx
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=True)

    # Detection results
    status = db.Column(db.String(30), default='pending')  # pending, processing, preview, completed, failed
    institution_detected = db.Column(db.String(100), nullable=True)
    account_number_detected = db.Column(db.String(50), nullable=True)
    statement_period_start = db.Column(db.Date, nullable=True)
    statement_period_end = db.Column(db.Date, nullable=True)

    # Processing stats
    total_records = db.Column(db.Integer, default=0)
    imported_count = db.Column(db.Integer, default=0)
    duplicate_count = db.Column(db.Integer, default=0)
    failed_count = db.Column(db.Integer, default=0)

    # Raw preview data (JSON)
    preview_data = db.Column(db.JSON, nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    wallet = db.relationship('Wallet', back_populates='import_jobs')
    transactions = db.relationship('Transaction', back_populates='import_job', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', back_populates='import_job', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.original_filename,
            'file_type': self.file_type,
            'wallet_id': self.wallet_id,
            'status': self.status,
            'institution_detected': self.institution_detected,
            'statement_period_start': self.statement_period_start.isoformat() if self.statement_period_start else None,
            'statement_period_end': self.statement_period_end.isoformat() if self.statement_period_end else None,
            'total_records': self.total_records,
            'imported_count': self.imported_count,
            'duplicate_count': self.duplicate_count,
            'failed_count': self.failed_count,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self):
        return f'<ImportJob {self.id} {self.original_filename}>'
