from flask import Blueprint, jsonify, request
from app import db
from app.auth_utils import jwt_required_with_user, get_current_organisation_id
from app.models import Asset, InventoryItem, User, Department

search_bp = Blueprint("search", __name__)

@search_bp.route("/", methods=["GET"])
@jwt_required_with_user
def global_search():
    """Global search across multiple entities."""
    org_id = get_current_organisation_id()
    query = request.args.get("q", "").strip()
    
    if not query or len(query) < 2:
        return jsonify({"assets": [], "inventory": [], "users": [], "departments": []}), 200

    search_pattern = f"%{query}%"

    # --- Phase 1: Search Base Entities & Gather IDs for IN operations ---
    
    # Departments
    departments_query = Department.query.filter(
        Department.organisation_id == org_id,
        Department.is_active == True,
        db.or_(
            Department.name.ilike(search_pattern),
            Department.code.ilike(search_pattern)
        )
    ).all()
    dept_ids = [d.id for d in departments_query]

    # Users
    users_query = User.query.filter(
        User.organisation_id == org_id,
        User.is_active == True,
        db.or_(
            User.username.ilike(search_pattern),
            User.email.ilike(search_pattern),
            User.first_name.ilike(search_pattern),
            User.last_name.ilike(search_pattern)
        )
    ).all()
    # We can track user names to search assigned assets
    user_names = [f"{u.first_name} {u.last_name}" for u in users_query]

    # --- Phase 2: Search Cross-Entities using IN operations and JOINs ---

    # Search Assets using joins to department and IN operations
    asset_conditions = [
        Asset.name.ilike(search_pattern),
        Asset.asset_code.ilike(search_pattern),
        Asset.serial_number.ilike(search_pattern)
    ]
    if dept_ids:
        asset_conditions.append(Asset.department_id.in_(dept_ids))
    if user_names:
        asset_conditions.append(Asset.assigned_to.in_(user_names))

    # Using outerjoin to eagerly fetch related department if needed (efficiency)
    assets_query = Asset.query.outerjoin(Department).filter(
        Asset.organisation_id == org_id,
        Asset.is_active == True,
        db.or_(*asset_conditions)
    ).limit(10).all()

    # Search Inventory
    inventory_query = InventoryItem.query.filter(
        InventoryItem.organisation_id == org_id,
        InventoryItem.is_active == True,
        db.or_(
            InventoryItem.name.ilike(search_pattern),
            InventoryItem.sku.ilike(search_pattern)
        )
    ).limit(10).all()

    # --- Phase 3: Format and Return ---
    
    return jsonify({
        "assets": [{"id": a.id, "name": a.name, "code": a.asset_code, "type": "Asset"} for a in assets_query[:5]],
        "inventory": [{"id": i.id, "name": i.name, "code": i.sku, "type": "Inventory"} for i in inventory_query[:5]],
        "users": [{"id": u.id, "name": f"{u.first_name} {u.last_name}", "code": u.email, "type": "User"} for u in users_query[:5]],
        "departments": [{"id": d.id, "name": d.name, "code": d.code, "type": "Department"} for d in departments_query[:5]]
    }), 200
