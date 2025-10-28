#!/usr/bin/env python3
"""Database models and setup for multi-user experiment tracking."""

from datetime import datetime
from pathlib import Path

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to experiments
    experiments = db.relationship("Experiment", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        """Hash and set the password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify a password against the hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """Convert user to dictionary (safe for JSON)."""
        return {
            "id": self.id,
            "username": self.username,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Experiment(db.Model):
    """Experiment model for tracking pipeline runs."""

    __tablename__ = "experiments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Paths
    input_path = db.Column(db.String(500), nullable=False)
    output_path = db.Column(db.String(500), nullable=False)
    
    # Parameters (stored as JSON)
    parameters = db.Column(db.JSON)
    
    # Execution info
    status = db.Column(db.String(20), default="created")  # created, running, completed, failed
    exit_code = db.Column(db.Integer)
    
    # Log file path
    log_file = db.Column(db.String(500))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    def to_dict(self) -> dict:
        """Convert experiment to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
            "name": self.name,
            "description": self.description,
            "input_path": self.input_path,
            "output_path": self.output_path,
            "parameters": self.parameters,
            "status": self.status,
            "exit_code": self.exit_code,
            "log_file": self.log_file,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


def init_db(app):
    """Initialize the database with the app."""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        
        # Create default users if none exist
        if User.query.count() == 0:
            create_default_users()


def create_default_users():
    """Create default user accounts."""
    default_users = [
        {"username": "admin", "password": "admin123"},
        {"username": "user1", "password": "user123"},
        {"username": "user2", "password": "user123"},
        {"username": "researcher", "password": "research123"},
    ]
    
    for user_data in default_users:
        user = User(username=user_data["username"])
        user.set_password(user_data["password"])
        db.session.add(user)
    
    try:
        db.session.commit()
        print("✓ Default users created successfully")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating default users: {e}")
