from datetime import datetime
from app import db
from app.models.asset import Asset
from app.models.scan_event import ScanEvent
from app.models.location_topology import WarehouseBin
from app.models.inventory import InventoryItem
from app.models.location_topology import Warehouse
from app.errors import NotFoundError, ValidationError
from app.utils.security import verify_signed_qr
from app.services.event_bus import event_bus
from app.audit_service import AuditService
from app.db_utils import transaction_retry


class TrackingService:
    """Service for managing item tracking via QR scans."""

    @staticmethod
    @transaction_retry(max_retries=3)
    def record_scan(
        org_id,
        user_id,
        qr_data,
        action_type,
        warehouse_id=None,
        bin_id=None,
        device_id=None,
        notes=None,
        lat=None,
        lon=None,
        session=None,
    ):
        """Record a scan event and update item location atomically."""
        sess = session or db.session

        # 1. Identify Item (Search Assets then Inventory Instances)
        item = None
        item_type = None

        # A. Verify QR Signature
        if ":" in qr_data and not qr_data.startswith(
            "{"
        ):  # Basic heuristic for signed format
            verified_payload = verify_signed_qr(qr_data)
            if not verified_payload:
                raise ValidationError("Invalid or tampered QR signature")
            qr_data = (
                verified_payload  # Use the verified payload as the search key
            )

        # B. Parse payload format: asset:<org_id>:<asset_code>
        if ":" in qr_data:
            parts = qr_data.split(":")
            if len(parts) >= 3 and parts[0] == "asset":
                target_org_id = int(parts[1])
                asset_code = parts[2]
                if target_org_id == org_id:
                    item = (
                        Asset.query.with_for_update()
                        .filter_by(
                            organisation_id=org_id, asset_code=asset_code
                        )
                        .first()
                    )
                    item_type = "asset"

        # C. Try to parse as JSON for smarter lookup (Legacy/Other)
        if not item:
            import json

            try:
                parsed = json.loads(qr_data)
                if (
                    isinstance(parsed, dict)
                    and "id" in parsed
                    and "type" in parsed
                ):
                    entity_id = parsed["id"]
                    if parsed["type"] == "asset":
                        item = (
                            Asset.query.with_for_update()
                            .filter_by(id=entity_id, organisation_id=org_id)
                            .first()
                        )
                        item_type = "asset"
                    elif parsed["type"] == "inventory":
                        from app.models.item_instance import (
                            ItemInstance,
                        )

                        instance = (
                            ItemInstance.query.with_for_update()
                            .join(InventoryItem)
                            .filter(
                                InventoryItem.organisation_id == org_id,
                                ItemInstance.id == entity_id,
                            )
                            .first()
                        )
                        if instance:
                            item = instance
                            item_type = "inventory_instance"
            except (json.JSONDecodeError, TypeError):
                pass

        # Fallback to direct string match if not found via JSON
        if not item:
            asset_obj = (
                Asset.query.with_for_update()
                .filter(
                    Asset.organisation_id == org_id,
                    db.or_(Asset.qr_code_data == qr_data, Asset.asset_code == qr_data)
                )
                .first()
            )
            if asset_obj:
                item = asset_obj
                item_type = "asset"
            else:
                from app.models.item_instance import ItemInstance

                instance = (
                    ItemInstance.query.with_for_update()
                    .join(InventoryItem)
                    .filter(
                        InventoryItem.organisation_id == org_id,
                        db.or_(ItemInstance.qr_code_data == qr_data, InventoryItem.sku == qr_data)
                    )
                    .first()
                )
                if instance:
                    item = instance
                    item_type = "inventory_instance"

        if not item:
            raise NotFoundError("No item found matching this QR code")

        # 2. Validate Location (if provided)
        if bin_id:
            from app.models.location_topology import (
                WarehouseBin,
                WarehouseShelf,
                WarehouseRack,
                WarehouseZone,
            )

            bin_obj = (
                WarehouseBin.query.join(WarehouseShelf)
                .join(WarehouseRack)
                .join(WarehouseZone)
                .join(Warehouse)
                .filter(
                    WarehouseBin.id == bin_id,
                    Warehouse.organisation_id == org_id,
                )
                .first()
            )

            if not bin_obj:
                raise ValidationError("Invalid storage bin or access denied")

            # Verify bin belongs to warehouse if warehouse_id is provided
            if warehouse_id:
                if bin_obj.shelf.rack.zone.warehouse_id != warehouse_id:
                    raise ValidationError(
                        "Storage bin does not belong to the selected warehouse"
                    )
            else:
                raise ValidationError(
                    "Warehouse ID is required when specifying a bin"
                )

        # 3. Create Scan Event
        event = ScanEvent(
            organisation_id=org_id,
            user_id=user_id,
            item_type=item_type,
            item_id=item.id,
            warehouse_id=warehouse_id,
            bin_id=bin_id,
            device_id=device_id,
            action_type=action_type,
            notes=notes,
            latitude=lat,
            longitude=lon,
            timestamp=datetime.utcnow(),
        )
        sess.add(event)

        # 4. Audit Log
        AuditService.log_action(
            action=f"QR_SCAN_{action_type}",
            entity_type=item_type,
            entity_id=item.id,
            details={
                "warehouse_id": warehouse_id,
                "bin_id": bin_id,
                "action": action_type,
                "notes": notes,
            },
            user_id=user_id,
            organisation_id=org_id,
            session=sess,
        )

        # 4. Update Item State
        if action_type == "CHECK_OUT":
            item.warehouse_id = None
            item.bin_id = None
            if item_type == "asset":
                item.location = "Checked Out"
        else:
            if warehouse_id is not None:
                item.warehouse_id = warehouse_id
            if bin_id is not None:
                item.bin_id = bin_id

        if item_type == "asset":
            # Update location string if warehouse/bin provided
            if warehouse_id:
                wh = Warehouse.query.get(warehouse_id)
                if wh:
                    item.location = f"WH: {wh.name}"
                    if bin_id:
                        item.location += f" / Bin: {bin_id}"

            # Asset state mapping
            if action_type == "CHECK_OUT":
                item.status = "in_use"
            elif action_type == "CHECK_IN":
                item.status = "approved"
            elif action_type == "TRANSFER":
                if item.status == "maintenance":
                    item.status = "approved"
            elif action_type == "AUDIT":
                pass

        else:  # inventory_instance
            # Inventory instance state mapping
            if action_type == "CHECK_OUT":
                item.status = "shipped"
            elif action_type == "CHECK_IN":
                item.status = "in_stock"
            elif action_type == "TRANSFER":
                item.status = "in_stock"
            elif action_type == "AUDIT":
                pass

        # Real-time Broadcast
        event_bus.publish(
            "SCAN_EVENT",
            {
                "item_id": item.id,
                "type": item_type,
                "warehouse_id": warehouse_id,
                "action": action_type,
                "lat": lat,
                "lon": lon,
                "timestamp": event.timestamp.isoformat()
            },
            organisation_id=org_id,
        )

        sess.commit()
        return item, event

    @staticmethod
    def get_history(org_id, item_type, item_id):
        """Get full movement history for an item."""
        return (
            ScanEvent.query.filter_by(
                organisation_id=org_id, item_type=item_type, item_id=item_id
            )
            .order_by(ScanEvent.timestamp.desc())
            .all()
        )

    @staticmethod
    def get_bin_environment(bin_id, org_id):
        """Get the surrounding environment of a bin, including nearby items."""
        bin_obj = WarehouseBin.query.get(bin_id)
        if not bin_obj:
            raise NotFoundError("Bin not found")

        # Find other items in the same bin or adjacent shelf
        nearby_assets = Asset.query.filter_by(
            organisation_id=org_id,
            location=f"WH: {bin_obj.shelf.rack.zone.warehouse.name} / Bin: {bin_id}",
        ).all()

        # In a real spatial system, we'd query by X,Y,Z range

        return {
            "bin_code": bin_obj.code,
            "coordinates": {
                "x": bin_obj.x_pos,
                "y": bin_obj.y_pos,
                "z": bin_obj.z_pos,
            },
            "environment_image": bin_obj.environment_image_url,
            "nearby_items_count": len(nearby_assets),
            "status": bin_obj.status,
        }
