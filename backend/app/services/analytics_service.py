from sqlalchemy import func
from app import db
from app.models import InventoryItem, StockMovement
from datetime import datetime, timedelta


class AnalyticsService:
    """Service for computing enterprise-grade analytics and KPIs."""

    @staticmethod
    def get_inventory_summary(org_id):
        """Get high-level inventory distribution (Health)."""
        # Count items by status/levels
        from app.models import RestockAlert

        total_items = InventoryItem.query.filter_by(
            organisation_id=org_id
        ).count()

        # Consolidate into a single aggregation query
        alert_counts = (
            db.session.query(
                RestockAlert.severity, func.count(RestockAlert.id)
            )
            .filter_by(organisation_id=org_id, status="PENDING")
            .group_by(RestockAlert.severity)
            .all()
        )

        counts_map = {severity: count for severity, count in alert_counts}

        low_stock = counts_map.get("LOW", 0)
        critical_stock = counts_map.get("CRITICAL", 0)
        out_of_stock = counts_map.get("OUT_OF_STOCK", 0)

        return {
            "total_items": total_items,
            "health": {
                "healthy": total_items
                - (low_stock + critical_stock + out_of_stock),
                "low": low_stock,
                "critical": critical_stock,
                "out_of_stock": out_of_stock,
            },
        }

    @staticmethod
    def get_warehouse_utilization(org_id):
        """Calculate bin occupancy per warehouse using a single aggregated query."""
        from app.models import (
            Warehouse,
            WarehouseBin,
            WarehouseZone,
            WarehouseRack,
            WarehouseShelf,
        )

        # Aggregate totals and occupied counts per warehouse
        results = (
            db.session.query(
                Warehouse.id,
                Warehouse.name,
                func.count(WarehouseBin.id).label("total_bins"),
                func.sum(
                    db.case((WarehouseBin.status == "occupied", 1), else_=0)
                ).label("occupied_bins"),
            )
            .select_from(Warehouse)
            .outerjoin(
                WarehouseZone, WarehouseZone.warehouse_id == Warehouse.id
            )
            .outerjoin(
                WarehouseRack, WarehouseRack.zone_id == WarehouseZone.id
            )
            .outerjoin(
                WarehouseShelf, WarehouseShelf.rack_id == WarehouseRack.id
            )
            .outerjoin(
                WarehouseBin, WarehouseBin.shelf_id == WarehouseShelf.id
            )
            .filter(Warehouse.organisation_id == org_id)
            .group_by(Warehouse.id, Warehouse.name)
            .all()
        )

        return [
            {
                "warehouse_id": r.id,
                "warehouse_name": r.name,
                "total_bins": r.total_bins,
                "occupied_bins": int(r.occupied_bins or 0),
                "utilization_percentage": (
                    round((int(r.occupied_bins or 0) / r.total_bins * 100), 1)
                    if r.total_bins > 0
                    else 0
                ),
            }
            for r in results
        ]

    @staticmethod
    def get_movement_trends(org_id, days=7):
        """Get daily movement volume for time-series charts."""
        threshold = datetime.utcnow() - timedelta(days=days)

        # Group by date and type
        movements = (
            db.session.query(
                func.date(StockMovement.date).label("day"),
                StockMovement.type,
                func.count(StockMovement.id).label("count"),
            )
            .join(InventoryItem)
            .filter(
                InventoryItem.organisation_id == org_id,
                StockMovement.date >= threshold,
            )
            .group_by("day", StockMovement.type)
            .all()
        )

        # Reformat for frontend charts
        results = {}
        # Pre-fill with last N days to ensure chart always has x-axis points
        for i in range(days):
            d = (datetime.utcnow() - timedelta(days=i)).date()
            results[str(d)] = {"IN": 0, "OUT": 0}

        for day, m_type, count in movements:
            d_str = str(day)
            if d_str in results:
                results[d_str][m_type] = count
            else:
                results[d_str] = {"IN": 0, "OUT": 0}
                results[d_str][m_type] = count

        return results

    @staticmethod
    def get_inventory_valuation(org_id):
        """Calculate total monetary value of inventory on hand."""
        value = (
            db.session.query(
                func.sum(InventoryItem.quantity * InventoryItem.unit_price)
            )
            .filter(InventoryItem.organisation_id == org_id)
            .scalar()
            or 0
        )

        return round(value, 2)
