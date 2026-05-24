import os
import uuid
import csv
from io import StringIO
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import Blueprint, jsonify, request, g, current_app, send_file
from app.auth_utils import jwt_required_with_user, require_role, get_current_organisation_id
from app.models.organization import Organization
from app.models.inventory import InventoryItem, StockMovement
from app.models.asset import Asset
from app.audit_service import AuditService
from app import db

settings_bp = Blueprint("settings", __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'svg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@settings_bp.route("/organization", methods=["GET"])
@jwt_required_with_user
def get_organization_settings():
    """Fetch the current organization's configuration."""
    org_id = get_current_organisation_id()
    org = Organization.query.get(org_id)
    if not org:
        return jsonify({"success": False, "message": "Organization not found"}), 404

    return jsonify({
        "success": True,
        "organization": {
            "id": org.id,
            "name": org.name,
            "code": org.code,
            "description": org.description,
            "logo_url": org.logo_url,
            "preferences": org.preferences or {},
            "is_active": org.is_active
        }
    }), 200

@settings_bp.route("/organization", methods=["PUT"])
@jwt_required_with_user
@require_role("admin")
def update_organization_settings():
    """Update the current organization's configuration."""
    org_id = get_current_organisation_id()
    org = Organization.query.get(org_id)
    if not org:
        return jsonify({"success": False, "message": "Organization not found"}), 404

    data = request.get_json()
    
    old_name = org.name
    
    if "name" in data and data["name"].strip():
        org.name = data["name"].strip()
        
    if "preferences" in data and isinstance(data["preferences"], dict):
        if org.preferences is None:
            org.preferences = {}
        # Merge preferences securely
        updated_prefs = dict(org.preferences)
        updated_prefs.update(data["preferences"])
        org.preferences = updated_prefs
        
    db.session.commit()
    
    # Log the settings change
    AuditService.log_action(
        action="UPDATE_SETTINGS",
        entity_type="organization",
        entity_id=org.id,
        details={"old_name": old_name, "new_name": org.name, "preferences_updated": "preferences" in data},
        user_id=g.user.id,
        organisation_id=org_id
    )
    
    # Real-time event
    from app.services.event_bus import event_bus
    event_bus.publish(
        "ORGANIZATION_UPDATE",
        {"name": org.name},
        organisation_id=org_id
    )

    return jsonify({
        "success": True,
        "message": "Organization settings updated successfully",
        "organization": {
            "id": org.id,
            "name": org.name,
            "code": org.code,
            "description": org.description,
            "logo_url": org.logo_url,
            "preferences": org.preferences
        }
    }), 200


@settings_bp.route("/organization", methods=["OPTIONS"])
def organization_options():
    """CORS preflight for organization settings endpoint."""
    return ('', 204)

@settings_bp.route("/organization/logo", methods=["POST"])
@jwt_required_with_user
@require_role("admin")
def upload_organization_logo():
    """Upload a physical image file for the organization logo."""
    org_id = get_current_organisation_id()
    org = Organization.query.get(org_id)
    if not org:
        return jsonify({"success": False, "message": "Organization not found"}), 404

    if 'logo' not in request.files:
        return jsonify({"success": False, "message": "No file part in the request"}), 400
        
    file = request.files['logo']
    if file.filename == '':
        return jsonify({"success": False, "message": "No selected file"}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Prepend a unique UUID to prevent overwriting existing files
        unique_filename = f"{org.code}_{uuid.uuid4().hex[:8]}_{filename}"
        
        # Ensure upload directory exists
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'logos')
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)
        
        # Update organization logo_url (relative path for frontend access)
        org.logo_url = f"/static/uploads/logos/{unique_filename}"
        db.session.commit()
        
        AuditService.log_action(
            action="UPLOAD_LOGO",
            entity_type="organization",
            entity_id=org.id,
            details={"logo_url": org.logo_url},
            user_id=g.user.id,
            organisation_id=org_id
        )
        
        from app.services.event_bus import event_bus
        event_bus.publish(
            "ORGANIZATION_UPDATE",
            {"logo_url": org.logo_url},
            organisation_id=org_id
        )
        
        return jsonify({
            "success": True,
            "message": "Logo uploaded successfully",
            "logo_url": org.logo_url
        }), 200
        
    return jsonify({"success": False, "message": "File type not allowed"}), 400


@settings_bp.route("/organization/logo", methods=["OPTIONS"])
def upload_organization_logo_options():
    """CORS preflight for logo upload endpoint."""
    return ('', 204)

@settings_bp.route("/organization/export", methods=["POST"])
@jwt_required_with_user
@require_role("admin")
def export_system_data():
    """Generate a downloadable CSV report of the organization's current assets and inventory items."""
    org_id = get_current_organisation_id()
    
    # Generate CSV in memory
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Type', 'ID', 'Name', 'SKU/Barcode', 'Status', 'Quantity/Value'])
    
    # Export Assets
    assets = Asset.query.filter_by(organisation_id=org_id).all()
    for a in assets:
        cw.writerow(['Asset', a.id, a.name, a.barcode, a.status, a.current_value])
        
    # Export Inventory
    inventory = InventoryItem.query.filter_by(organisation_id=org_id).all()
    for i in inventory:
        cw.writerow(['Inventory', i.id, i.name, i.sku, i.status, i.quantity])
        
    AuditService.log_action(
        action="DATA_EXPORT",
        entity_type="organization",
        entity_id=org_id,
        details={"records_exported": len(assets) + len(inventory)},
        user_id=g.user.id,
        organisation_id=org_id
    )
        
    output = si.getvalue()
    si.close()
    
    return output, 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename=export_org_{org_id}_{datetime.now().strftime("%Y%m%d")}.csv'
    }


@settings_bp.route("/organization/export", methods=["OPTIONS"])
def export_system_data_options():
    """CORS preflight for data export endpoint."""
    return ('', 204)

@settings_bp.route("/organization/purge", methods=["DELETE"])
@jwt_required_with_user
@require_role("admin")
def purge_historical_data():
    """Permanently delete movement logs older than 3 years to satisfy data compliance."""
    org_id = get_current_organisation_id()
    
    # Calculate cutoff date (3 years ago)
    cutoff_date = datetime.utcnow() - timedelta(days=3 * 365)
    
    # Find inventory items for the org
    items = InventoryItem.query.filter_by(organisation_id=org_id).all()
    item_ids = [item.id for item in items]
    
    deleted_count = 0
    if item_ids:
        # Delete movements
        deleted_count = StockMovement.query.filter(
            StockMovement.item_id.in_(item_ids),
            StockMovement.date < cutoff_date
        ).delete(synchronize_session=False)
        db.session.commit()
        
    AuditService.log_action(
        action="DATA_PURGE",
        entity_type="organization",
        entity_id=org_id,
        details={"records_deleted": deleted_count, "cutoff_date": cutoff_date.isoformat()},
        user_id=g.user.id,
        organisation_id=org_id
    )
    
    return jsonify({
        "success": True,
        "message": f"Successfully purged {deleted_count} historical records.",
        "records_deleted": deleted_count
    }), 200


@settings_bp.route("/organization/purge", methods=["OPTIONS"])
def purge_historical_data_options():
    """CORS preflight for organization purge endpoint."""
    return ('', 204)
