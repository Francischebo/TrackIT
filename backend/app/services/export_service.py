import csv
import io
from datetime import datetime
from app.models import StockMovement, InventoryItem


class ExportService:
    """Service for generating enterprise reports and data exports."""

    @staticmethod
    def export_movement_history(org_id, days=30):
        """Generate a CSV export of movement history using a generator."""
        from datetime import timedelta

        threshold = datetime.utcnow() - timedelta(days=days)

        # Stream from database
        from sqlalchemy.orm import joinedload

        movements = (
            StockMovement.query.options(joinedload(StockMovement.item))
            .join(InventoryItem)
            .filter(
                InventoryItem.organisation_id == org_id,
                StockMovement.date >= threshold,
            )
            .order_by(StockMovement.date.desc())
            .yield_per(100)
        )

        def generate():
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(
                ["Date", "Item", "SKU", "Type", "Quantity", "Reference"]
            )
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

            for m in movements:
                writer.writerow(
                    [
                        m.date.isoformat(),
                        m.item.name,
                        m.item.sku,
                        m.type,
                        m.quantity,
                        m.reference or "",
                    ]
                )
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)

        return generate()

    @staticmethod
    def export_inventory_valuation(org_id):
        """Generate a valuation report using a generator."""
        items = InventoryItem.query.filter_by(
            organisation_id=org_id
        ).yield_per(100)

        def generate():
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(
                ["Item", "SKU", "Quantity", "Unit Price", "Total Value"]
            )
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

            for item in items:
                writer.writerow(
                    [
                        item.name,
                        item.sku,
                        item.quantity,
                        item.unit_price,
                        round(item.quantity * item.unit_price, 2),
                    ]
                )
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)

        return generate()
