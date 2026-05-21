from flask import current_app
from sqlalchemy import text
from app import db

from app.tenant_migrations import initialize_tenant_schema


def set_tenant_schema(organisation_id):
    """
    Set the database search path to the tenant's specific schema.
    This ensures physical data isolation between institutions in PostgreSQL.
    """
    if not organisation_id:
        return

    # Skip for SQLite as it doesn't support schemas in the same way
    db_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri.startswith("sqlite"):
        return

    schema_name = f"tenant_{organisation_id:04d}"
    
    try:
        # Set the search_path to the tenant's schema first, then public for shared tables
        db.session.execute(text(f"SET search_path TO {schema_name}, public"))
        current_app.logger.debug(f"Database search_path set to {schema_name}")
    except Exception as e:
        current_app.logger.error(f"Failed to set database search_path: {str(e)}")
        # In production, we might want to raise an error here to prevent data leaks
        if not current_app.debug:
            raise e


def create_tenant_schema(organisation_id):
    """
    Create a new schema for a newly registered institution and initialize tables.

    This uses a lightweight tenant migration runner (app.tenant_migrations.initialize_tenant_schema)
    which creates the schema and applies an initial migration under an advisory lock to avoid
    race conditions when multiple app instances attempt to provision the same tenant concurrently.
    """
    return initialize_tenant_schema(organisation_id)
