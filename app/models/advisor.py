from datetime import datetime

from app.extensions import db


class AdvisorConversation(db.Model):
    __tablename__ = 'advisor_conversations'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(128), nullable=False, unique=True, index=True)
    title = db.Column(db.String(200), nullable=False, default='Financial Advisor')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = db.relationship('AdvisorMessage', back_populates='conversation', cascade='all, delete-orphan', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'title': self.title,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class AdvisorMessage(db.Model):
    __tablename__ = 'advisor_messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('advisor_conversations.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    conversation = db.relationship('AdvisorConversation', back_populates='messages')

    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
