from flask import Blueprint, g, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app import db
from app.audit_service import AuditService
from app.auth_utils import (
    get_current_organisation_id,
    jwt_required_with_user,
    require_role,
)
from app.db_utils import transaction_retry
from app.errors import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.models import asset, organization, transfer
from app.validation import (
    TransferRequestSchema,
    TransferReviewSchema,
    validate_input,
)

transfers_bp = Blueprint("transfers", __name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


@transfers_bp.route("/request", methods=["POST"])
@jwt_required_with_user
@require_role("admin", "staff", "dept_head")
@limiter.limit("20 per minute")
@transaction_retry(max_retries=3)
def request_transfer():
    """Request transfer of asset between departments"""
    data = request.get_json()
    org_id = get_current_organisation_id()

    # Validate input
    validated_data, errors = validate_input(TransferRequestSchema, data)
    if errors:
        raise ValidationError("Validation failed", errors)

    # Get asset
    asset_obj = asset.Asset.query.filter_by(
        id=validated_data["asset_id"], organisation_id=org_id
    ).first()

    if not asset_obj:
        raise NotFoundError("Asset not found")

    # Check if asset can be transferred (not disposed)
    if asset_obj.status == "disposed":
        raise ValidationError("Cannot transfer a disposed asset")

    # Check if new department exists and belongs to organization
    new_dept = organization.Department.query.filter_by(
        id=validated_data["new_department_id"],
        organisation_id=org_id,
        is_active=True,
    ).first()

    if not new_dept:
        raise ValidationError("Invalid destination department")

    # Check if transfer already requested
    existing_request = transfer.TransferRequest.query.filter_by(
        asset_id=validated_data["asset_id"], 
        organisation_id=org_id,
        status="pending"
    ).first()

    if existing_request:
        raise ConflictError("Transfer already requested for this asset")

    # Create transfer request
    transfer_request = transfer.TransferRequest(
        organisation_id=org_id,
        asset_id=validated_data["asset_id"],
        requested_by=g.user.id,
        from_department_id=asset_obj.department_id,
        to_department_id=validated_data["new_department_id"],
        requested_location=validated_data.get("new_location"),
        to_warehouse_id=validated_data.get("to_warehouse_id"),
        to_bin_id=validated_data.get("to_bin_id"),
        comment=validated_data.get("comment"),
    )

    db.session.add(transfer_request)
    # Audit log
    AuditService.log_action(
        action="TRANSFER_REQUESTED",
        entity_type="transfer_request",
        entity_id=transfer_request.id,
        details={
            "asset_id": asset_obj.id,
            "asset_code": asset_obj.asset_code,
            "from_department": asset_obj.department_id,
            "to_department": validated_data["new_department_id"],
            "requested_by": g.user.username,
        },
        organisation_id=org_id,
    )

    db.session.commit()

    return (
        jsonify(
            {
                "message": "Transfer request submitted successfully",
                "request_id": transfer_request.id,
            }
        ),
        201,
    )


@transfers_bp.route("/history/<int:asset_id>", methods=["GET"])
@jwt_required_with_user
@limiter.limit("50 per minute")
def get_transfer_history(asset_id):
    """Get transfer history for an asset"""
    org_id = get_current_organisation_id()

    # Verify asset belongs to organization
    asset_obj = asset.Asset.query.filter_by(
        id=asset_id,
        organisation_id=org_id,
    ).first()

    if not asset_obj:
        raise NotFoundError("Asset not found")

    # Get transfer history from audit logs
    from app.models import inventory

    transfer_logs = (
        inventory.AuditLog.query.filter(
            inventory.AuditLog.organisation_id == org_id,
            inventory.AuditLog.entity_type == "asset",
            inventory.AuditLog.entity_id == asset_id,
            inventory.AuditLog.action == "ASSET_TRANSFER",
        )
        .order_by(inventory.AuditLog.created_at.desc())
        .all()
    )

    history = []
    for log in transfer_logs:
        details = log.details or {}
        history.append(
            {
                "id": log.id,
                "timestamp": log.created_at.isoformat(),
                "from_department": details.get("from_department"),
                "to_department": details.get("to_department"),
                "old_location": details.get("old_location"),
                "new_location": details.get("new_location"),
                "transferred_by": details.get("transferred_by"),
                "user_id": log.user_id,
            }
        )

    return (
        jsonify(
            {
                "asset_id": asset_id,
                "asset_code": asset_obj.asset_code,
                "asset_name": asset_obj.name,
                "current_department": asset_obj.department_id,
                "current_location": asset_obj.location,
                "transfer_history": history,
            }
        ),
        200,
    )


@transfers_bp.route("/requests", methods=["GET"])
@jwt_required_with_user
@limiter.limit("50 per minute")
def get_transfer_requests():
    """Get transfer requests for current user's organization"""
    org_id = get_current_organisation_id()

    # Query parameters
    status = request.args.get("status", "pending")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    from sqlalchemy.orm import joinedload

    query = transfer.TransferRequest.query.options(
        joinedload(transfer.TransferRequest.asset),
        joinedload(transfer.TransferRequest.requester),
        joinedload(transfer.TransferRequest.reviewer),
        joinedload(transfer.TransferRequest.from_department),
        joinedload(transfer.TransferRequest.to_department),
    ).filter_by(organisation_id=org_id)

    if status:
        query = query.filter_by(status=status)

    # Filter based on user role
    if g.user.role not in ["admin"]:
        # Non-admins can only see requests they created or for
        # departments they head
        headed_dept_ids = [d.id for d in g.user.headed_departments]
        query = query.filter(
            db.or_(
                transfer.TransferRequest.requested_by == g.user.id,
                transfer.TransferRequest.from_department_id.in_(
                    headed_dept_ids
                ),
                transfer.TransferRequest.to_department_id.in_(headed_dept_ids),
            )
        )

    requests = query.order_by(
        transfer.TransferRequest.requested_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return (
        jsonify(
            {
                "transfer_requests": [
                    {
                        "id": r.id,
                        "asset_id": r.asset_id,
                        "asset_code": r.asset.asset_code if r.asset else None,
                        "asset_name": r.asset.name if r.asset else None,
                        "from_department": r.from_department_id,
                        "from_department_name": (
                            r.from_department.name
                            if r.from_department
                            else None
                        ),
                        "to_department": r.to_department_id,
                        "to_department_name": (
                            r.to_department.name if r.to_department else None
                        ),
                        "requested_location": r.requested_location,
                        "comment": r.comment,
                        "status": r.status,
                        "requested_by": (
                            r.requester.username if r.requester else None
                        ),
                        "requested_at": r.requested_at.isoformat(),
                        "reviewed_by": (
                            r.reviewer.username if r.reviewer else None
                        ),
                        "reviewed_at": (
                            r.reviewed_at.isoformat()
                            if r.reviewed_at
                            else None
                        ),
                        "review_comments": r.review_comments,
                    }
                    for r in requests.items
                ],
                "pagination": {
                    "page": requests.page,
                    "per_page": requests.per_page,
                    "total": requests.total,
                    "pages": requests.pages,
                    "has_next": requests.has_next,
                    "has_prev": requests.has_prev,
                },
            }
        ),
        200,
    )


@transfers_bp.route("/bulk", methods=["POST"])
@jwt_required_with_user
@require_role("admin")
@limiter.limit("10 per minute")
def bulk_transfer():
    """Bulk transfer multiple assets to a department"""
    data = request.get_json()
    org_id = get_current_organisation_id()

    asset_ids = data.get("asset_ids", [])
    new_department_id = data.get("new_department_id")
    new_location = data.get("new_location")

    if not asset_ids or not new_department_id:
        raise ValidationError("asset_ids and new_department_id are required")

    # Validate department
    new_dept = organization.Department.query.filter_by(
        id=new_department_id, organisation_id=org_id, is_active=True
    ).first()

    if not new_dept:
        raise ValidationError("Invalid destination department")

    # Get assets
    assets_to_transfer = asset.Asset.query.filter(
        asset.Asset.id.in_(asset_ids), asset.Asset.organisation_id == org_id
    ).all()

    if len(assets_to_transfer) != len(asset_ids):
        raise ValidationError(
            "Some assets not found or don't belong to your organization"
        )

    # Check if any assets are disposed
    disposed_assets = [a for a in assets_to_transfer if a.status == "disposed"]
    if disposed_assets:
        disposed_codes = [a.asset_code for a in disposed_assets]
        raise ValidationError(
            f"Cannot transfer disposed assets: {disposed_codes}"
        )

    # Perform bulk transfer
    transferred_assets = []
    for asset_obj in assets_to_transfer:
        old_dept_id = asset_obj.department_id
        old_location = asset_obj.location

        asset_obj.department_id = new_department_id
        asset_obj.location = new_location or asset_obj.location
        asset_obj.updated_at = db.func.now()

        transferred_assets.append(
            {
                "id": asset_obj.id,
                "asset_code": asset_obj.asset_code,
                "old_department": old_dept_id,
                "new_department": new_department_id,
                "old_location": old_location,
                "new_location": asset_obj.location,
            }
        )

    db.session.commit()

    # Audit log for bulk transfer
    AuditService.log_action(
        action="BULK_ASSET_TRANSFER",
        entity_type="transfer",
        entity_id=None,
        details={
            "transferred_assets": transferred_assets,
            "new_department": new_department_id,
            "new_location": new_location,
            "transferred_by": g.user.username,
            "count": len(transferred_assets),
        },
        organisation_id=org_id,
    )

    return (
        jsonify(
            {
                "message": (
                    f"Successfully transferred {len(transferred_assets)} assets"
                ),
                "transferred_assets": transferred_assets,
            }
        ),
        200,
    )


@transfers_bp.route("/requests/<int:request_id>/approve", methods=["POST"])
@jwt_required_with_user
@require_role("admin", "dept_head")
@limiter.limit("20 per minute")
@transaction_retry(max_retries=3)
def approve_transfer_request(request_id):
    """Approve a transfer request"""
    data = request.get_json() or {}
    org_id = get_current_organisation_id()

    validated_data, errors = validate_input(TransferReviewSchema, data)
    if errors:
        raise ValidationError("Validation failed", errors)

    # Get transfer request with lock
    transfer_req = (
        transfer.TransferRequest.query.with_for_update()
        .filter_by(id=request_id, organisation_id=org_id, status="pending")
        .first()
    )

    if not transfer_req:
        raise NotFoundError("Transfer request not found")

    # Check permissions
    if g.user.role not in ["admin"]:
        # Department heads can only approve transfers from/to departments
        # they head
        if transfer_req.from_department_id not in [
            d.id for d in g.user.headed_departments
        ] and transfer_req.to_department_id not in [
            d.id for d in g.user.headed_departments
        ]:
            raise AuthorizationError(
                "You can only approve transfers for departments you head"
            )

    # Get asset with lock
    asset_obj = (
        asset.Asset.query.with_for_update()
        .filter_by(id=transfer_req.asset_id, organisation_id=org_id)
        .first()
    )
    if not asset_obj:
        raise NotFoundError("Asset not found")

    # Perform transfer
    old_dept_id = asset_obj.department_id
    old_location = asset_obj.location

    asset_obj.department_id = transfer_req.to_department_id
    asset_obj.location = transfer_req.requested_location or asset_obj.location
    asset_obj.warehouse_id = (
        transfer_req.to_warehouse_id or asset_obj.warehouse_id
    )
    asset_obj.bin_id = transfer_req.to_bin_id or asset_obj.bin_id
    asset_obj.updated_at = db.func.now()

    # Update transfer request
    transfer_req.status = "approved"
    transfer_req.reviewed_by = g.user.id
    transfer_req.reviewed_at = db.func.now()
    transfer_req.review_comments = validated_data.get("comments")

    # Audit logs
    AuditService.log_transfer(
        asset_obj,
        old_dept_id,
        transfer_req.to_department_id,
        details={
            "transfer_request_id": transfer_req.id,
            "approved_by": g.user.username,
            "old_location": old_location,
            "new_location": asset_obj.location,
            "comments": transfer_req.review_comments,
        },
    )

    AuditService.log_action(
        action="TRANSFER_REQUEST_APPROVED",
        entity_type="transfer_request",
        entity_id=transfer_req.id,
        details={"asset_id": asset_obj.id, "approved_by": g.user.username},
        organisation_id=org_id,
    )

    db.session.commit()

    return (
        jsonify(
            {
                "message": "Transfer request approved successfully",
                "asset_id": asset_obj.id,
                "transfer_request_id": transfer_req.id,
            }
        ),
        200,
    )


@transfers_bp.route("/requests/<int:request_id>/reject", methods=["POST"])
@jwt_required_with_user
@require_role("admin", "dept_head")
@limiter.limit("20 per minute")
@transaction_retry(max_retries=3)
def reject_transfer_request(request_id):
    """Reject a transfer request"""
    data = request.get_json() or {}
    org_id = get_current_organisation_id()

    validated_data, errors = validate_input(TransferReviewSchema, data)
    if errors:
        raise ValidationError("Validation failed", errors)

    # Get transfer request with lock
    transfer_req = (
        transfer.TransferRequest.query.with_for_update()
        .filter_by(id=request_id, organisation_id=org_id, status="pending")
        .first()
    )

    if not transfer_req:
        raise NotFoundError("Transfer request not found")

    # Check permissions
    if g.user.role not in ["admin"]:
        # Department heads can only reject transfers from/to departments
        # they head
        if transfer_req.from_department_id not in [
            d.id for d in g.user.headed_departments
        ] and transfer_req.to_department_id not in [
            d.id for d in g.user.headed_departments
        ]:
            raise AuthorizationError(
                "You can only reject transfers for departments you head"
            )

    # Update transfer request
    transfer_req.status = "rejected"
    transfer_req.reviewed_by = g.user.id
    transfer_req.reviewed_at = db.func.now()
    transfer_req.review_comments = validated_data.get("comments")

    # Audit log
    AuditService.log_action(
        action="TRANSFER_REQUEST_REJECTED",
        entity_type="transfer_request",
        entity_id=transfer_req.id,
        details={
            "asset_id": transfer_req.asset_id,
            "rejected_by": g.user.username,
            "comments": transfer_req.review_comments,
        },
        organisation_id=org_id,
    )

    db.session.commit()

    return (
        jsonify(
            {
                "message": "Transfer request rejected",
                "transfer_request_id": transfer_req.id,
            }
        ),
        200,
    )
