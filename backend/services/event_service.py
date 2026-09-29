import sys
import os

# --------------------------------------------------
# PROJECT ROOT
# --------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

sys.path.insert(0, BASE_DIR)

# --------------------------------------------------
# DATABASE IMPORT
# --------------------------------------------------

from database.database import SessionLocal
from database.models import Event

# --------------------------------------------------
# DATABASE SESSION
# --------------------------------------------------

def get_session():

    return SessionLocal()


# --------------------------------------------------
# CONVERT DATABASE EVENT
# --------------------------------------------------

def event_to_dict(event):

    extra_data = {}

    if event.extra_data:

        try:
            import json

            extra_data = json.loads(
                event.extra_data
            )

        except Exception:

            extra_data = {}


    return {

        "event_id": event.event_id,

        "event_type": event.event_type,

        "confidence": event.confidence,

        "bus_id": event.bus_id,

        "video_timestamp": event.video_timestamp,

        "latitude": event.latitude,

        "longitude": event.longitude,

        "severity": event.severity,

        "detected_at": event.detected_at,

        "evidence_image": event.evidence_image,

        "priority": event.priority,

        "status": event.status,

        "action_required": event.action_required,

        "alert_message": event.alert_message,

        "extra_data": extra_data
    }


# --------------------------------------------------
# GET ALL EVENTS
# --------------------------------------------------

def get_all_events():

    db = get_session()

    try:

        events = (
            db.query(Event)
            .order_by(Event.detected_at.desc())
            .all()
        )

        return [
            event_to_dict(event)
            for event in events
        ]

    finally:

        db.close()

# --------------------------------------------------
# GET EVENT BY ID
# --------------------------------------------------

def get_event_by_id(event_id):

    db = get_session()

    try:

        event = (
            db.query(Event)
            .filter(
                Event.event_id == event_id
            )
            .first()
        )

        if not event:
            return None

        return event_to_dict(event)

    finally:

        db.close()
# --------------------------------------------------
# GET EVENTS BY TYPE
# --------------------------------------------------

def get_events_by_type(event_type):

    db = get_session()

    try:

        events = (
            db.query(Event)
            .filter(
                Event.event_type == event_type
            )
            .order_by(Event.video_timestamp)
            .all()
        )

        return [
            event_to_dict(event)
            for event in events
        ]

    finally:

        db.close()


# --------------------------------------------------
# HIGH PRIORITY EVENTS
# --------------------------------------------------

def get_high_priority_events():

    db = get_session()

    try:

        events = (
            db.query(Event)
            .filter(
                Event.priority == 3
            )
            .order_by(Event.video_timestamp)
            .all()
        )

        return [
            event_to_dict(event)
            for event in events
        ]

    finally:

        db.close()


# --------------------------------------------------
# EVENT SUMMARY
# --------------------------------------------------

def get_summary():

    db = get_session()

    try:

        total = db.query(Event).count()

        potholes = (
            db.query(Event)
            .filter(
                Event.event_type == "pothole"
            )
            .count()
        )

        waterlogging = (
            db.query(Event)
            .filter(
                Event.event_type == "waterlogging"
            )
            .count()
        )

        traffic = (
            db.query(Event)
            .filter(
                Event.event_type == "traffic"
            )
            .count()
        )

        high = (
            db.query(Event)
            .filter(
                Event.priority == 3
            )
            .count()
        )

        medium = (
            db.query(Event)
            .filter(
                Event.priority == 2
            )
            .count()
        )

        low = (
            db.query(Event)
            .filter(
                Event.priority == 1
            )
            .count()
        )


        return {

            "total_events": total,

            "potholes": potholes,

            "waterlogging": waterlogging,

            "traffic": traffic,

            "high_priority": high,

            "medium_priority": medium,

            "low_priority": low
        }

    finally:

        db.close()

# --------------------------------------------------
# SAVE EVENT TO DATABASE
# --------------------------------------------------

def save_event(event_data):

    db = get_session()

    try:

        import json

        # ------------------------------------------
        # Generate next event ID
        # ------------------------------------------

        last_event = (
            db.query(Event)
            .order_by(Event.id.desc())
            .first()
        )

        if last_event:

            next_number = last_event.id + 1

        else:

            next_number = 1

        event_id = (
            f"EVT-{next_number:04d}"
        )

        # ------------------------------------------
        # Priority
        # ------------------------------------------

        severity = event_data.get(
            "severity",
            "MEDIUM"
        )

        if severity == "HIGH":

            priority = 3

        elif severity == "MEDIUM":

            priority = 2

        else:

            priority = 1

        # ------------------------------------------
        # Alert message
        # ------------------------------------------

        event_type = event_data.get(
            "event_type"
        )

        alert_messages = {

            "pothole":
                "Road pothole detected",

            "waterlogging":
                "Waterlogging detected on road",

            "traffic":
                "Traffic congestion detected",

            "number_plate":
                "Vehicle number plate detected"
        }

        alert_message = alert_messages.get(
            event_type,
            "AI event detected"
        )

        # ------------------------------------------
        # Create database object
        # ------------------------------------------

        db_event = Event(

            event_id=event_id,

            event_type=event_data.get(
                "event_type"
            ),

            confidence=event_data.get(
                "confidence"
            ),

            bus_id=event_data.get(
                "bus_id"
            ),

            video_timestamp=event_data.get(
                "video_timestamp"
            ),

            latitude=event_data.get(
                "latitude"
            ),

            longitude=event_data.get(
                "longitude"
            ),

            severity=severity,

            detected_at=event_data.get(
                "detected_at"
            ),

            evidence_image=event_data.get(
                "evidence_image"
            ),

            priority=priority,

            status="NEW",

            action_required=True,

            alert_message=alert_message,

            extra_data=json.dumps(
                event_data.get(
                    "extra_data",
                    {}
                )
            )
        )

        # ------------------------------------------
        # INSERT
        # ------------------------------------------

        db.add(db_event)

        db.commit()

        db.refresh(db_event)

        return event_to_dict(db_event)

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# --------------------------------------------------
# SERVICE TEST
# --------------------------------------------------

if __name__ == "__main__":

    print("============================================")
    print(" SMART BUS DATABASE EVENT SERVICE")
    print("============================================")
    print()

    events = get_all_events()

    print(
        f"Events loaded from database: {len(events)}"
    )

    print()

    summary = get_summary()

    print("Event Summary")
    print("--------------------------------------------")

    print(
        f"Total:        {summary['total_events']}"
    )

    print(
        f"Potholes:     {summary['potholes']}"
    )

    print(
        f"Waterlogging: {summary['waterlogging']}"
    )

    print(
        f"Traffic:      {summary['traffic']}"
    )

    print(
        f"High:         {summary['high_priority']}"
    )

    print(
        f"Medium:       {summary['medium_priority']}"
    )

    print(
        f"Low:          {summary['low_priority']}"
    )

    print()
    print("============================================")
    print(" DATABASE EVENT SERVICE TEST COMPLETE")
    print("============================================")