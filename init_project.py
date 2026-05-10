#!/usr/bin/env python3
"""
TrackIT initialization script
Creates full project structure from scratch
"""

import os
from datetime import datetime
from pathlib import Path


def create_project_structure():
    """Create all necessary directories and files"""

    root = Path(__file__).parent

    # Define all directories to create
    dirs = [
        "app",
        "app/models",
        "app/blueprints",
        "app/templates",
        "app/static",
        "app/static/css",
        "app/static/js",
        "migrations",
    ]

    print("Creating directories...")
    for d in dirs:
        path = root / d
        path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {d}/")

    # Create app/__init__.py
    app_init_code = '''from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name=None):
    """Application factory"""
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
'''

    # Create app/models/__init__.py
    models_init_code = "# Models package\\n"

    # Create app/models/user.py
    user_code = '''from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    """User model with Flask-Login integration"""
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
        """Hash and set password"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, action, resource=None):
        """Check if user has permission for action"""
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
'''

    # Create app/models/organization.py
    org_code = '''from app import db
from datetime import datetime

class Organization(db.Model):
    """Multi-tenant organization model"""
    __tablename__ = 'organizations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    code = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    users = db.relationship('User', backref='organization', lazy=True)
    departments = db.relationship('Department', backref='organization', lazy=True, cascade='all, delete-orphan')
    assets = db.relationship('Asset', backref='organization', lazy=True, cascade='all, delete-orphan')
    inventory_items = db.relationship('InventoryItem', backref='organization', lazy=True, cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='organization', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Organization {self.code}>'


class Department(db.Model):
    """Department model for organizing assets"""
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    head_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('organisation_id', 'code', name='uq_dept_org_code'),
    )
    
    assets = db.relationship('Asset', backref='department', lazy=True)
    head = db.relationship('User', backref='headed_departments', foreign_keys=[head_id])
    
    def __repr__(self):
        return f'<Department {self.code}>'
'''

    # Create app/models/asset.py
    asset_code = '''from app import db
from datetime import datetime, timedelta
from enum import Enum

class AssetStatus(Enum):
    """Asset status enumeration"""
    REQUESTED = 'requested'
    APPROVED = 'approved'
    IN_USE = 'in_use'
    MAINTENANCE = 'maintenance'
    DISPOSED = 'disposed'

class AssetCondition(Enum):
    """Asset condition enumeration"""
    NEW = 'new'
    GOOD = 'good'
    FAIR = 'fair'
    REPAIR = 'repair'
    CONDEMNED = 'condemned'

class DepreciationMethod(Enum):
    """Depreciation method enumeration"""
    STRAIGHT_LINE = 'straight_line'

class Asset(db.Model):
    """Asset model for tracking fixed assets"""
    __tablename__ = 'assets'
    
    id = db.Column(db.Integer, primary_key=True)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    asset_code = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    serial_number = db.Column(db.String(255))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    assigned_to = db.Column(db.String(255))
    status = db.Column(db.String(50), nullable=False, default=AssetStatus.REQUESTED.value)
    condition = db.Column(db.String(50), nullable=False, default=AssetCondition.NEW.value)
    location = db.Column(db.String(255))
    purchase_date = db.Column(db.Date, nullable=False)
    purchase_value = db.Column(db.Float, nullable=False)
    useful_life = db.Column(db.Integer, nullable=False)
    depreciation_method = db.Column(db.String(50), nullable=False, default=DepreciationMethod.STRAIGHT_LINE.value)
    current_value = db.Column(db.Float, nullable=False)
    qr_code_data = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('organisation_id', 'asset_code', name='uq_asset_org_code'),
        db.UniqueConstraint('organisation_id', 'serial_number', name='uq_asset_org_serial'),
    )
    
    audit_logs = db.relationship('AssetAuditLog', backref='asset', lazy=True, cascade='all, delete-orphan')
    
    def can_transition_to(self, new_status):
        """Validate state transition"""
        current = self.status
        new = new_status if isinstance(new_status, str) else new_status.value
        
        allowed_transitions = {
            AssetStatus.REQUESTED.value: [AssetStatus.APPROVED.value],
            AssetStatus.APPROVED.value: [AssetStatus.IN_USE.value],
            AssetStatus.IN_USE.value: [AssetStatus.MAINTENANCE.value, AssetStatus.DISPOSED.value],
            AssetStatus.MAINTENANCE.value: [AssetStatus.IN_USE.value],
            AssetStatus.DISPOSED.value: []
        }
        
        return new in allowed_transitions.get(current, [])
    
    def update_current_value(self):
        """Calculate current value using straight-line depreciation"""
        if self.depreciation_method != DepreciationMethod.STRAIGHT_LINE.value:
            return
        
        years_used = (datetime.utcnow().date() - self.purchase_date).days / 365.25
        annual_depreciation = self.purchase_value / self.useful_life
        depreciated_value = self.purchase_value - (annual_depreciation * years_used)
        
        self.current_value = max(0, depreciated_value)
    
    def __repr__(self):
        return f'<Asset {self.asset_code}>'


class AssetAuditLog(db.Model):
    """Audit log for asset changes"""
    __tablename__ = 'asset_audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AssetAuditLog {self.asset_id} - {self.action}>'
'''

    # Create app/models/inventory.py
    inventory_code = '''from app import db
from datetime import datetime
from enum import Enum

class StockMovementType(Enum):
    """Stock movement type enumeration"""
    IN = 'IN'
    OUT = 'OUT'

class InventoryItem(db.Model):
    """Inventory item model for consumable inventory"""
    __tablename__ = 'inventory_items'
    
    id = db.Column(db.Integer, primary_key=True)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    sku = db.Column(db.String(100))
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=10)
    unit_price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('organisation_id', 'sku', name='uq_inventory_org_sku'),
        db.CheckConstraint('quantity >= 0', name='ck_inventory_quantity_nonneg'),
        db.CheckConstraint('reorder_level >= 0', name='ck_inventory_reorder_nonneg'),
    )
    
    stock_movements = db.relationship('StockMovement', backref='inventory_item', lazy=True, cascade='all, delete-orphan')
    
    def add_stock(self, quantity):
        """Add stock (IN movement)"""
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
        self.quantity += quantity
        movement = StockMovement(
            item_id=self.id,
            type=StockMovementType.IN.value,
            quantity=quantity,
            date=datetime.utcnow()
        )
        db.session.add(movement)
    
    def remove_stock(self, quantity):
        """Remove stock (OUT movement)"""
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
        if self.quantity < quantity:
            raise ValueError("Insufficient stock")
        self.quantity -= quantity
        movement = StockMovement(
            item_id=self.id,
            type=StockMovementType.OUT.value,
            quantity=quantity,
            date=datetime.utcnow()
        )
        db.session.add(movement)
    
    def is_low_stock(self):
        """Check if stock is below reorder level"""
        return self.quantity < self.reorder_level
    
    def __repr__(self):
        return f'<InventoryItem {self.name}>'


class StockMovement(db.Model):
    """Stock movement log for inventory tracking"""
    __tablename__ = 'stock_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    reference = db.Column(db.String(255))
    notes = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.CheckConstraint("type IN ('IN', 'OUT')", name='ck_stock_movement_type'),
        db.CheckConstraint('quantity > 0', name='ck_stock_movement_qty_positive'),
    )
    
    def __repr__(self):
        return f'<StockMovement {self.item_id} - {self.type}>'


class AuditLog(db.Model):
    """General audit log for system-wide actions"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(100))
    entity_id = db.Column(db.Integer)
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AuditLog {self.action} - {self.entity_type}>'
'''

    files = [
        ("app/__init__.py", app_init_code),
        ("app/models/__init__.py", models_init_code),
        ("app/models/user.py", user_code),
        ("app/models/organization.py", org_code),
        ("app/models/asset.py", asset_code),
        ("app/models/inventory.py", inventory_code),
        ("app/blueprints/__init__.py", "# Blueprints package\\n"),
    ]

    print("\\nCreating Python files...")
    for filename, content in files:
        filepath = root / filename
        filepath.write_text(content)
        print(f"  ✓ {filename}")

    print("\\n✓ Project structure initialized successfully!")
    return True


if __name__ == "__main__":
    try:
        create_project_structure()
        print("\\nNext steps:")
        print("  1. pip install -r requirements.txt")
        print("  2. python db_seed.py")
        print("  3. python run.py")
    except Exception as e:
        print(f"✗ Error: {e}")
        exit(1)
