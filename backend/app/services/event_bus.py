import json
import time
from datetime import datetime, timedelta
from app import db
from app.models.event import SystemEvent


class EventBus:
    """Robust Event Bus using Database Polling for multi-process scalability."""

    def publish(self, event_type, data, organisation_id=None):
        """Publish an event by persisting it to the database for all workers to see."""
        event = SystemEvent(
            event_type=event_type, data=data, organisation_id=organisation_id
        )
        db.session.add(event)
        db.session.commit()

    def stream(self, organisation_id=None):
        """Streaming generator that polls for events. SSE compatible."""
        # Initial offset
        last_check = datetime.utcnow()
        last_id = 0

        while True:
            # Re-scoping session to get fresh data
            db.session.expire_all()

            # Polling logic: fetch events newer than last check
            query = SystemEvent.query.filter(
                SystemEvent.created_at >= last_check - timedelta(seconds=5)
            )

            if organisation_id:
                query = query.filter(
                    (SystemEvent.organisation_id == organisation_id)
                    | (SystemEvent.organisation_id == None)
                )

            if last_id > 0:
                query = query.filter(SystemEvent.id > last_id)

            events = query.order_by(SystemEvent.id.asc()).limit(50).all()

            for event in events:
                yield f"data: {json.dumps(event.to_dict())}\n\n"
                last_id = event.id
                last_check = event.created_at

            # Sleep to prevent high DB load
            time.sleep(1)


# Global singleton
event_bus = EventBus()
