from flask import current_app, g
from sqlalchemy import text
from app import db

def set_tenant_schema(organisation_id):
    """
    Set the database search path to the tenant's specific schema.
    This ensures physical data isolation between institutions in PostgreSQL.
    """
    if not organisation_id:
        return

    # Skip for SQLite as it doesn't support schemas in the same way
    db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_uri.startswith('sqlite'):
        return

    schema_name = f"tenant_{organisation_id:04d}"
    
    try:
        # Set the search_path to the tenant's schema first, then public for shared tables
        db.session.execute(text(f'SET search_path TO {schema_name}, public'))
        current_app.logger.debug(f"Database search_path set to {schema_name}")
    except Exception as e:
        current_app.logger.error(f"Failed to set database search_path: {str(e)}")
        # In production, we might want to raise an error here to prevent data leaks
        if not current_app.debug:
            raise e

def create_tenant_schema(organisation_id):
    """
    Create a new schema for a newly registered institution and initialize tables.
    """
    db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_uri.startswith('sqlite'):
        return True # SQLite handled via row-level isolation

    schema_name = f"tenant_{organisation_id:04d}"
    
    try:
        # 1. Create the schema
        db.session.execute(text(f'CREATE SCHEMA IF NOT EXISTS {schema_name}'))
        db.session.commit()
        
        # 2. Initialize tenant-specific tables in this schema
        # Note: In a production app, we would run migrations here.
        # For this setup, we'll ensure the search path is set and use SQLAlchemy's create_all
        original_search_path = db.session.execute(text('SHOW search_path')).scalar()
        
        db.session.execute(text(f'SET search_path TO {schema_name}'))
        
        # We only want to create tenant-specific tables here
        # For simplicity, we create all, but PostgreSQL will prioritize the search path
        from app.models import (
            Asset, AssetAuditLog, InventoryItem, WarehouseStock,
            Warehouse, WarehouseBin, TransferRequest, Department,
            StockMovement, AuditLog, RestockAlert, ScanEvent, ItemInstance
        )
        
        # This will create tables in the current search_path (the new schema)
        db.create_all()
        
        # Restore original search path
        db.session.execute(text(f'SET search_path TO {original_search_path}'))
        db.session.commit()
        
        current_app.logger.info(f"Initialized schema {schema_name} for organization {organisation_id}")
        return True
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to initialize schema {schema_name}: {str(e)}")
        return False
