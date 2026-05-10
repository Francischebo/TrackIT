#!/usr/bin/env python3
"""Setup script - creates directories and project structure"""

import os
import sys
from pathlib import Path

# Get the project root (where this script is)
project_root = Path(__file__).parent

# Create directories
directories = [
    project_root / "app",
    project_root / "app" / "models",
    project_root / "app" / "blueprints",
    project_root / "app" / "templates",
    project_root / "app" / "static",
]

for directory in directories:
    directory.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created: {directory}")

# Create __init__.py files
app_init = """from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name=None):
    \"\"\"Application factory\"\"\"
    app = Flask(__name__)
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    from config import config_by_name
    app.config.from_object(config_by_name[config_name])
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    with app.app_context():
        from app.models import user, organization, asset, inventory
        
        @login_manager.user_loader
        def load_user(user_id):
            return user.User.query.get(int(user_id))
        
        db.create_all()
    
    return app
"""

models_init = "# Models package\\n"

user_model = """from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    \"\"\"User model with Flask-Login integration\"\"\"
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    username = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    role = db.Column(db.String(50), nullable=False, default='staff')
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('organisation_id', 'username', name='uq_user_org_username'),
        db.UniqueConstraint('organisation_id', 'email', name='uq_user_org_email'),
    )
    
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)
    
    def set_password(self, password):
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, action, resource=None):
        permissions = {
            'admin': ['create', 'edit', 'delete', 'approve', 'view'],
            'staff': ['create', 'edit', 'view'],
            'viewer': ['view'],
            'auditor': ['view'],
            'dept_head': ['approve', 'view'],
            'store_manager': ['create', 'edit', 'view']
        }
        return action in permissions.get(self.role, [])
    
    def __repr__(self):
        return f'<User {self.username}>'
"""

# Write all files
files_to_create = [
    (project_root / "app" / "__init__.py", app_init),
    (project_root / "app" / "models" / "__init__.py", models_init),
    (project_root / "app" / "models" / "user.py", user_model),
]

for filepath, content in files_to_create:
    filepath.write_text(content)
    print(f"✓ Created: {filepath.relative_to(project_root)}")

print("\\n✓ Project structure created successfully!")
print(f"✓ Project root: {project_root}")
