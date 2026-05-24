from flask import Blueprint, g, jsonify, request
from app.auth_utils import jwt_required_with_user, get_current_organisation_id
from app.services.tracking_service import TrackingService
from app.services.anomaly_service import AnomalyService
from app.errors import ValidationError
from app.validation import validate_input, sanitize_string
from marshmallow import Schema, fields

tracking_bp = Blueprint("tracking", __name__)


class ScanRequestSchema(Schema):
    qr_data = fields.String(required=True)
    action_type = fields.String(
        required=True
    )  # CHECK_IN, CHECK_OUT, TRANSFER, AUDIT
    warehouse_id = fields.Integer()
    bin_id = fields.Integer()
    device_id = fields.String()
    notes = fields.String()
    lat = fields.Float()
    lon = fields.Float()


@tracking_bp.route("/scan", methods=["POST"])
@jwt_required_with_user
def record_scan():
    """Endpoint for processing a QR scan event."""
    data = request.get_json()
    org_id = get_current_organisation_id()

    validated_data, errors = validate_input(ScanRequestSchema, data)
    if errors:
        raise ValidationError("Validation failed", errors)

    # Sanitize notes
    if "notes" in validated_data:
        validated_data["notes"] = sanitize_string(validated_data["notes"])

    # Record scan
    item, event = TrackingService.record_scan(
        org_id=org_id, user_id=g.user.id, **validated_data
    )

    # Get recent history for visual trace
    history = TrackingService.get_history(org_id, event.item_type, item.id)

    # Perform AI analysis
    anomalies = AnomalyService.analyze_scan(event)

    return (
        jsonify(
            {
                "message": "Scan recorded successfully",
                "item": {
                    "type": event.item_type,
                    "id": item.id,
                    "status": item.status,
                },
                "history": [
                    {
                        "timestamp": h.timestamp.isoformat(),
                        "action": h.action_type,
                        "latitude": h.latitude,
                        "longitude": h.longitude,
                        "warehouse_id": h.warehouse_id,
                        "bin_id": h.bin_id,
                    }
                    for h in history
                ],
                "anomalies": anomalies,
            }
        ),
        200,
    )


@tracking_bp.route("/scan", methods=["OPTIONS"])
def record_scan_options():
    """CORS preflight for scan endpoint."""
    return ('', 204)


@tracking_bp.route("/bin-environment/<int:bin_id>", methods=["GET"])
@jwt_required_with_user
def get_bin_environment(bin_id):
    """Get the surrounding environment of a bin."""
    org_id = get_current_organisation_id()
    env_data = TrackingService.get_bin_environment(bin_id, org_id)
    return jsonify(env_data), 200


@tracking_bp.route(
    "/history/<string:item_type>/<int:item_id>", methods=["GET"]
)
@jwt_required_with_user
def get_item_history(item_type, item_id):
    """Get movement history for an item."""
    org_id = get_current_organisation_id()
    history = TrackingService.get_history(org_id, item_type, item_id)

    return (
        jsonify(
            {
                "item_type": item_type,
                "item_id": item_id,
                "history": [
                    {
                        "timestamp": h.timestamp.isoformat(),
                        "action": h.action_type,
                        "warehouse_id": h.warehouse_id,
                        "bin_id": h.bin_id,
                        "user_id": h.user_id,
                        "notes": h.notes,
                    }
                    for h in history
                ],
            }
        ),
        200,
    )
