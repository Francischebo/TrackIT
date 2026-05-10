from app import db
from app.audit_service import AuditService
from app.repositories.asset_repository import AssetRepository
from app.models import organization
from app.utils.security import generate_signed_qr
from app.errors import NotFoundError, ConflictError, ValidationError
from app.db_utils import transaction_retry
from datetime import datetime
from app.services.event_bus import event_bus

class AssetService:
    """Service layer for asset business logic."""

    def __init__(self, repository: AssetRepository = None, session=None):
        self.repo = repository or AssetRepository()
        self.session = session or db.session

    def list_assets(
        self,
        org_id,
        page=1,
        per_page=50,
        status=None,
        department_id=None,
        search=None,
    ):
        return self.repo.list_assets(
            org_id,
            page=page,
            per_page=per_page,
            status=status,
            department_id=department_id,
            search=search,
        )

    def get_asset(self, asset_id, org_id):
        asset_obj = self.repo.get_asset(asset_id, org_id)
        if not asset_obj:
            raise NotFoundError("Asset not found")
        return asset_obj

    @transaction_retry(max_retries=3)
    def create_asset(self, org_id, validated_data):
        # validate department exists
        dept = organization.Department.query.filter_by(
            id=validated_data["department_id"], organisation_id=org_id
        ).first()
        if not dept:
            raise ValidationError("Invalid department")

        # Purchase date cannot be in the future
        if validated_data["purchase_date"] > datetime.utcnow().date():
            raise ValidationError("Purchase date cannot be in the future")

        # Get organization for code prefix
        org = organization.Organization.query.get(org_id)
        if not org:
            raise ValidationError("Organization not found")

        # 1. Auto-generate Asset Code if missing (e.g., ORG-001)
        if not validated_data.get("asset_code"):
            asset_count = self.repo.count_assets(org_id)
            new_code = f"{org.code}-{str(asset_count + 1).zfill(3)}"
            
            # Ensure uniqueness (loop in case of race/deletion)
            while self.repo.exists_asset_code(org_id, new_code):
                asset_count += 1
                new_code = f"{org.code}-{str(asset_count + 1).zfill(3)}"
            
            validated_data["asset_code"] = new_code
        else:
            if self.repo.exists_asset_code(org_id, validated_data["asset_code"]):
                raise ConflictError("Asset code already exists")

        if validated_data.get("serial_number") and self.repo.exists_serial(
            org_id, validated_data.get("serial_number")
        ):
            raise ConflictError("Serial number already exists")

        # Generate signed QR code data using system URL for security
        # Format: https://trackit.app/tracking?qr_payload=asset:<org_id>:<asset_code>
        # Note: We still sign the inner payload for integrity
        inner_payload = f"asset:{org_id}:{validated_data['asset_code']}"
        signed_payload = generate_signed_qr(inner_payload)
        
        # We store the full URL in qr_code_data
        # In production, this base URL should be in config
        base_url = "http://localhost:5173/tracking" # Development default
        validated_data["qr_code_data"] = f"{base_url}?data={signed_payload}"

        new_asset = self.repo.create_asset(
            org_id, validated_data, session=self.session
        )
        # set initial current value via model method
        new_asset.update_current_value()
        AuditService.log_asset_change(
            new_asset,
            "ASSET_CREATED",
            new_values={
                "asset_code": new_asset.asset_code,
                "name": new_asset.name,
                "department_id": new_asset.department_id,
            },
            session=self.session,
        )
        self.session.commit()
        
        event_bus.publish("ASSET_CREATED", {"asset_id": new_asset.id, "asset_code": new_asset.asset_code}, organisation_id=org_id)
        
        return new_asset

    @transaction_retry(max_retries=3)
    def update_asset(self, asset_id, org_id, data):
        # Reload with lock
        from app.models.asset import Asset

        asset_obj = (
            Asset.query.with_for_update()
            .filter_by(id=asset_id, organisation_id=org_id)
            .first()
        )
        if not asset_obj:
            raise NotFoundError("Asset not found")

        old_values = {
            "name": asset_obj.name,
            "department_id": asset_obj.department_id,
            "assigned_to": asset_obj.assigned_to,
            "location": asset_obj.location,
            "condition": asset_obj.condition,
        }

        if "department_id" in data:
            dept = organization.Department.query.filter_by(
                id=data["department_id"], organisation_id=org_id
            ).first()
            if not dept:
                raise ValidationError("Invalid department")

        updatable_fields = {
            k: data[k]
            for k in ["name", "assigned_to", "location", "condition"]
            if k in data
        }
        self.repo.update_asset(asset_obj, updatable_fields)
        if "department_id" in data:
            asset_obj.department_id = data["department_id"]

        asset_obj.updated_at = db.func.now()
        AuditService.log_asset_change(
            asset_obj,
            "ASSET_UPDATED",
            old_values=old_values,
            new_values={k: getattr(asset_obj, k) for k in old_values.keys()},
            session=self.session,
        )
        self.session.commit()
        
        event_bus.publish("ASSET_UPDATED", {"asset_id": asset_obj.id}, organisation_id=org_id)
        
        return asset_obj

    @transaction_retry(max_retries=3)
    def update_asset_status(
        self, asset_id, org_id, new_status, current_user_role, comments=None
    ):
        # Reload with lock
        from app.models.asset import Asset

        asset_obj = (
            Asset.query.with_for_update()
            .filter_by(id=asset_id, organisation_id=org_id)
            .first()
        )
        if not asset_obj:
            raise NotFoundError("Asset not found")

        old_status = asset_obj.status
        if not asset_obj.can_transition_to(new_status):
            raise ValidationError(
                f"Invalid status transition from {old_status} to {new_status}"
            )

        # role checks are done at controller earlier; service just applies change
        asset_obj.status = new_status
        asset_obj.updated_at = db.func.now()
        AuditService.log_asset_change(
            asset_obj,
            "ASSET_STATUS_CHANGED",
            old_values={"status": old_status},
            new_values={"status": new_status},
            session=self.session,
        )
        self.session.commit()
        
        event_bus.publish("ASSET_STATUS_CHANGED", {"asset_id": asset_obj.id, "status": new_status}, organisation_id=org_id)
        
        return asset_obj

    def delete_asset(self, asset_id, org_id):
        asset_obj = self.repo.get_asset(asset_id, org_id)
        if not asset_obj:
            raise NotFoundError("Asset not found")

        if asset_obj.status in ["in_use", "maintenance"]:
            raise ConflictError(
                "Cannot delete asset that is in use or under maintenance"
            )

        # store audit data before delete
        asset_data = {
            "asset_code": asset_obj.asset_code,
            "name": asset_obj.name,
            "status": asset_obj.status,
        }
        self.repo.delete_asset(asset_obj, session=self.session)
        AuditService.log_action(
            action="ASSET_DELETED",
            entity_type="asset",
            entity_id=asset_obj.id,
            details=asset_data,
            organisation_id=asset_obj.organisation_id,
            session=self.session,
        )
        self.session.commit()
        
        event_bus.publish("ASSET_DELETED", {"asset_id": asset_id}, organisation_id=org_id)
        
        return True

    def stats(self, org_id):
        """Get asset statistics from repository"""
        return self.repo.stats(org_id)

    def get_bulk_qr_data(self, org_id, asset_ids=None):
        """Get data for bulk QR generation"""
        assets = self.repo.list_assets_by_ids(org_id, asset_ids) if asset_ids else self.repo.list_all_assets(org_id)
        return [
            {
                "id": a.id,
                "asset_code": a.asset_code,
                "name": a.name,
                "qr_code_data": a.qr_code_data
            }
            for a in assets
        ]
