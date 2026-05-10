from datetime import datetime
from enum import Enum

from app import db
from app.db_utils import transaction_retry


class StockMovementType(Enum):
    """Stock movement type enumeration"""

    IN = "IN"
    OUT = "OUT"


class InventoryItem(db.Model):
    """Inventory item model for consumable inventory"""

    __tablename__ = "inventory_items"

    id = db.Column(db.Integer, primary_key=True)
    organisation_id = db.Column(
        db.Integer, db.ForeignKey("organizations.id"), nullable=False
    )
    name = db.Column(db.String(255), nullable=False)
    sku = db.Column(db.String(100))
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=10)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    unit = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        db.UniqueConstraint(
            "organisation_id", "sku", name="uq_inventory_org_sku"
        ),
        db.CheckConstraint(
            "quantity >= 0", name="ck_inventory_quantity_nonneg"
        ),
        db.CheckConstraint(
            "reorder_level >= 0", name="ck_inventory_reorder_nonneg"
        ),
        db.Index("ix_inventory_org_id", "organisation_id"),
        db.Index("ix_inventory_sku", "sku"),
        db.Index("ix_inventory_active", "is_active"),
        db.Index(
            "ix_inventory_low_stock_query",
            "organisation_id",
            "is_active",
            "quantity",
            "reorder_level",
        ),
    )

    stock_movements = db.relationship(
        "StockMovement",
        backref="inventory_item",
        lazy=True,
        cascade="all, delete-orphan",
    )

    # Cascade delete for warehouse levels and alerts
    warehouse_stocks = db.relationship(
        "WarehouseStock",
        backref="item",
        lazy=True,
        cascade="all, delete-orphan",
    )

    restock_alerts = db.relationship(
        "RestockAlert", backref="item", lazy=True, cascade="all, delete-orphan"
    )

    @transaction_retry(max_retries=3)
    def add_stock(self, quantity, reference=None, notes=None):
        """Add stock (IN movement) with row-level locking"""
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")

        # Reload with lock
        item = InventoryItem.query.with_for_update().get(self.id)
        item.quantity += quantity

        movement = StockMovement(
            item_id=self.id,
            type=StockMovementType.IN.value,
            quantity=quantity,
            reference=reference,
            notes=notes,
            date=db.func.now(),
        )
        db.session.add(movement)

        # Trigger health check
        from app.services.restock_service import RestockService

        RestockService.evaluate_stock_health(self.id)

    @transaction_retry(max_retries=3)
    def remove_stock(self, quantity, reference=None, notes=None):
        """Remove stock (OUT movement) with row-level locking"""
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")

        # Reload with lock
        item = InventoryItem.query.with_for_update().get(self.id)
        if item.quantity < quantity:
            raise ValueError("Insufficient stock")

        item.quantity -= quantity
        movement = StockMovement(
            item_id=self.id,
            type=StockMovementType.OUT.value,
            quantity=quantity,
            reference=reference,
            notes=notes,
            date=db.func.now(),
        )
        db.session.add(movement)

        # Trigger health check
        from app.services.restock_service import RestockService

        RestockService.evaluate_stock_health(self.id)

    def is_low_stock(self):
        """Check if stock is below reorder level"""
        return self.quantity < self.reorder_level

    def __repr__(self):
        return f"<InventoryItem {self.name}>"


class StockMovement(db.Model):
    """Stock movement log for inventory tracking"""

    __tablename__ = "stock_movements"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(
        db.Integer, db.ForeignKey("inventory_items.id"), nullable=False
    )
    type = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    reference = db.Column(db.String(255))
    notes = db.Column(db.Text)

    __table_args__ = (
        db.Index("ix_stock_movements_date", "date"),
        db.Index("ix_stock_movements_item_date", "item_id", "date"),
        db.Index("ix_stock_movements_type", "type"),
    )
    date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint(
            "type IN ('IN', 'OUT')", name="ck_stock_movement_type"
        ),
        db.CheckConstraint(
            "quantity > 0", name="ck_stock_movement_qty_positive"
        ),
        db.Index("ix_stock_movements_item_id", "item_id"),
        db.Index("ix_stock_movements_type", "type"),
        db.Index("ix_stock_movements_date", "date"),
    )

    def __repr__(self):
        return f"<StockMovement {self.item_id} - {self.type}>"


class AuditLog(db.Model):
    """General audit log for system-wide actions"""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    organisation_id = db.Column(
        db.Integer, db.ForeignKey("organizations.id"), nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(100))
    entity_id = db.Column(db.Integer)
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index("ix_audit_logs_org_id", "organisation_id"),
        db.Index("ix_audit_logs_user_id", "user_id"),
        db.Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        db.Index("ix_audit_logs_action", "action"),
        db.Index("ix_audit_logs_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<AuditLog {self.action} - {self.entity_type}>"
