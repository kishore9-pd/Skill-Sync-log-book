"""
TECHWING Daily Training Logbook & Conversational AI System
SQLAlchemy Database Models & Schema Definitions
"""

import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    combo = db.Column(db.String(255), nullable=False, index=True)
    pin_number = db.Column(db.String(255), nullable=True)
    password_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='USER', index=True) # 'USER' or 'ADMIN'
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    daily_logs = db.relationship('DailyLog', backref='user', lazy=True, cascade="all, delete-orphan")
    login_activities = db.relationship('LoginActivity', backref='user', lazy=True, cascade="all, delete-orphan")
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)
    suggestions = db.relationship('Suggestion', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_college_pin(self, pin):
        self.pin_number = generate_password_hash(pin)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'combo': self.combo,
            'pin_masked': '**********' if self.pin_number else None,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'last_login_at': self.last_login_at.strftime('%Y-%m-%d %H:%M:%S') if self.last_login_at else None
        }


class DailyLog(db.Model):
    __tablename__ = 'daily_logs'

    id = db.Column(db.String(255), primary_key=True) # e.g. log_1789468624
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    user_email = db.Column(db.String(255), nullable=False, index=True)
    combo = db.Column(db.String(255), nullable=False, index=True)
    log_date = db.Column(db.String(50), nullable=False, index=True)
    day = db.Column(db.String(50), nullable=True)
    lab = db.Column(db.String(255), nullable=True)
    check_in = db.Column(db.String(50), nullable=True)
    check_out = db.Column(db.String(50), nullable=True)
    trainer = db.Column(db.String(255), nullable=True)
    topics = db.Column(db.Text, nullable=True)
    practical = db.Column(db.Text, nullable=True)
    assignment = db.Column(db.Text, nullable=True)
    doubts = db.Column(db.Text, nullable=True)
    important_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_user_logdate', 'user_id', 'log_date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_email': self.user_email,
            'combo': self.combo,
            'date': self.log_date,
            'day': self.day or '',
            'lab': self.lab or '',
            'checkIn': self.check_in or '',
            'checkOut': self.check_out or '',
            'trainer': self.trainer or '',
            'topics': self.topics or '',
            'practical': self.practical or '',
            'assignment': self.assignment or '',
            'doubts': self.doubts or '',
            'important_notes': self.important_notes or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class Suggestion(db.Model):
    __tablename__ = 'suggestions'

    id = db.Column(db.String(255), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    date = db.Column(db.String(50), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    category = db.Column(db.String(255), nullable=False, index=True)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    target_whatsapp = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default='Received', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date,
            'name': self.name,
            'email': self.email,
            'category': self.category,
            'subject': self.subject,
            'message': self.message,
            'target_whatsapp': self.target_whatsapp or '',
            'status': self.status or 'Received'
        }


class LoginActivity(db.Model):
    __tablename__ = 'login_activity'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    login_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    logout_time = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(100), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_email': self.user.email if self.user else None,
            'login_time': self.login_time.strftime('%Y-%m-%d %H:%M:%S') if self.login_time else None,
            'logout_time': self.logout_time.strftime('%Y-%m-%d %H:%M:%S') if self.logout_time else None,
            'ip_address': self.ip_address or '',
            'user_agent': self.user_agent or ''
        }


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    user_email = db.Column(db.String(255), nullable=True)
    action = db.Column(db.String(100), nullable=False, index=True) # LOGIN, LOG_CREATED, LOG_UPDATED, SUGGESTION_CREATED, etc.
    target_type = db.Column(db.String(100), nullable=True)
    target_id = db.Column(db.String(255), nullable=True)
    metadata_json = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        meta = {}
        if self.metadata_json:
            try:
                meta = json.loads(self.metadata_json)
            except Exception:
                meta = {'raw': self.metadata_json}
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_email': self.user_email or '',
            'action': self.action,
            'target_type': self.target_type or '',
            'target_id': self.target_id or '',
            'metadata': meta,
            'ip_address': self.ip_address or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
