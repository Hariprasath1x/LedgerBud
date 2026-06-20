from datetime import datetime
from app.extensions import db


class Goal(db.Model):
    __tablename__ = 'goals'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    target_amount = db.Column(db.Numeric(15, 2), nullable=False)
    current_amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    target_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='active')  # active, completed, paused
    color = db.Column(db.String(20), default='#6c63ff')
    icon = db.Column(db.String(50), default='target')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def progress_percentage(self):
        if self.target_amount and float(self.target_amount) > 0:
            return min(100.0, (float(self.current_amount) / float(self.target_amount)) * 100)
        return 0.0

    @property
    def remaining_amount(self):
        return max(0.0, float(self.target_amount) - float(self.current_amount))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'target_amount': float(self.target_amount),
            'current_amount': float(self.current_amount),
            'remaining_amount': self.remaining_amount,
            'progress_percentage': self.progress_percentage,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'status': self.status,
            'color': self.color,
            'icon': self.icon,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Goal {self.name} {self.progress_percentage:.1f}%>'
