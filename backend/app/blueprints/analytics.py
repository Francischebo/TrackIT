from datetime import datetime
from flask import Blueprint, jsonify, Response, request
from app.auth_utils import (
    jwt_required_with_user,
    get_current_organisation_id,
    require_role,
)
from app.services.analytics_service import AnalyticsService
from app.services.export_service import ExportService
from app.services.event_bus import event_bus

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/dashboard/summary", methods=["GET"])
@jwt_required_with_user
@require_role("admin", "store_manager", "auditor")
def get_summary():
    """Get high-level dashboard KPIs."""
    org_id = get_current_organisation_id()
    warehouse_id = request.args.get('warehouse_id', type=int)

    inventory = AnalyticsService.get_inventory_summary(org_id, warehouse_id=warehouse_id)
    valuation = AnalyticsService.get_inventory_valuation(org_id, warehouse_id=warehouse_id)
    assets = AnalyticsService.get_asset_summary(org_id, warehouse_id=warehouse_id)
    geospatial = AnalyticsService.get_geospatial_stats(org_id)
    compliance = AnalyticsService.get_compliance_stats(org_id)
    recent_activity = AnalyticsService.get_recent_activity(org_id, limit=7)
    movement_stats = AnalyticsService.get_movement_trends(org_id, days=7)
    insights = AnalyticsService.generate_insights(org_id)

    from flask import g
    from app.models.organization import Organization
    org = Organization.query.get(org_id)
    currency = org.preferences.get("currency", "KES") if org and org.preferences else "KES"

    # Robust calculation of total valuation (Inventory + Assets)
    try:
        inv_val = float(valuation or 0)
        asset_val = float(assets.get("total_current_value", 0)) if isinstance(assets, dict) else 0.0
        total_valuation = inv_val + asset_val
    except (TypeError, ValueError):
        total_valuation = 0.0

    return (
        jsonify(
            {
                "inventory": inventory,
                "total_valuation": total_valuation,
                "currency": currency,
                "assets": assets,
                "geospatial": geospatial,
                "compliance": compliance,
                "recent_activity": recent_activity,
                "movement_stats": movement_stats,
                "insights": insights
            }
        ),
        200,
    )


@analytics_bp.route("/dashboard/movements", methods=["GET"])
@jwt_required_with_user
@require_role("admin", "store_manager", "auditor")
def get_movement_trends():
    """Get inventory movement trends for charts."""
    org_id = get_current_organisation_id()
    days = request.args.get("days", 7, type=int)
    trends = AnalyticsService.get_movement_trends(org_id, days=days)
    return jsonify(trends), 200


@analytics_bp.route("/dashboard/warehouses", methods=["GET"])
@jwt_required_with_user
@require_role("admin", "store_manager", "auditor")
def get_warehouses_stats():
    """Get warehouse utilization metrics."""
    org_id = get_current_organisation_id()
    stats = AnalyticsService.get_warehouse_utilization(org_id)
    return jsonify(stats), 200


@analytics_bp.route("/export/movement", methods=["GET"])
@jwt_required_with_user
@require_role("admin", "store_manager")
def export_movement():
    """Export movement history as CSV."""
    org_id = get_current_organisation_id()
    generator = ExportService.export_movement_history(org_id)
    return Response(
        generator,
        mimetype="text/csv",
        headers={
            "Content-disposition": f"attachment; filename=movements_{datetime.utcnow().date()}.csv"
        },
    )


@analytics_bp.route("/export/valuation", methods=["GET"])
@jwt_required_with_user
@require_role("admin", "store_manager")
def export_valuation():
    """Export inventory valuation as CSV."""
    org_id = get_current_organisation_id()
    generator = ExportService.export_inventory_valuation(org_id)
    return Response(
        generator,
        mimetype="text/csv",
        headers={
            "Content-disposition": f"attachment; filename=valuation_{datetime.utcnow().date()}.csv"
        },
    )


@analytics_bp.route("/stream", methods=["GET"])
@jwt_required_with_user
def stream_events():
    """Real-time event stream (SSE)."""
    org_id = get_current_organisation_id()
    return Response(
        event_bus.stream(organisation_id=org_id), mimetype="text/event-stream"
    )
