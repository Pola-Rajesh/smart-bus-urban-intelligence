import json
import sys
from pathlib import Path
from datetime import datetime


# --------------------------------------------------
# PROJECT ROOT
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --------------------------------------------------
# DATABASE IMPORT
# --------------------------------------------------

from database.database import SessionLocal
from database.models import Event
# --------------------------------------------------
# EVENT ID GENERATOR
# --------------------------------------------------

def generate_event_id(db):

    last_event = (
        db.query(Event)
        .order_by(Event.id.desc())
        .first()
    )

    if last_event is None:
        return "EVT-0001"

    next_number = last_event.id + 1

    return f"EVT-{next_number:04d}"


# --------------------------------------------------
# PRIORITY CALCULATION
# --------------------------------------------------

def calculate_priority(event_type, confidence):

    if event_type in ["pothole", "waterlogging"]:

        if confidence >= 0.65:
            return 3, "HIGH"

        return 2, "MEDIUM"

    if event_type == "traffic":

        return 2, "MEDIUM"

    return 1, "LOW"


# --------------------------------------------------
# ALERT MESSAGE
# --------------------------------------------------

def create_alert_message(event_type):

    messages = {

        "pothole":
            "Road pothole detected",

        "waterlogging":
            "Waterlogging detected on road",

        "traffic":
            "Traffic congestion detected",

        "hit_and_run":
            "Possible hit-and-run incident detected"

    }

    return messages.get(
        event_type,
        "Urban incident detected"
    )


# --------------------------------------------------
# CREATE EVENT
# --------------------------------------------------

def create_event(
    event_type,
    confidence,
    bus_id,
    video_timestamp,
    latitude,
    longitude,
    evidence_image=None,
    extra_data=None,
    session_id=None
):

    db = SessionLocal()

    try:

        # ------------------------------------------
        # CHECK REQUIRED VALUES
        # ------------------------------------------

        if not event_type:
            raise ValueError(
                "event_type is required"
            )

        if not bus_id:
            raise ValueError(
                "bus_id is required"
            )

        if latitude is None or longitude is None:
            raise ValueError(
                "GPS coordinates are required"
            )


        # ------------------------------------------
        # GENERATE EVENT INFORMATION
        # ------------------------------------------

        event_id = generate_event_id(db)

        priority, severity = calculate_priority(
            event_type,
            confidence
        )

        alert_message = create_alert_message(
            event_type
        )


        # ------------------------------------------
        # CREATE DATABASE OBJECT
        # ------------------------------------------

        event = Event(

            event_id=event_id,

            session_id=session_id,

            event_type=event_type,

            confidence=confidence,

            bus_id=bus_id,

            video_timestamp=video_timestamp,

            latitude=latitude,

            longitude=longitude,

            severity=severity,

            detected_at=datetime.now(),

            evidence_image=evidence_image,

            priority=priority,

            status="NEW",

            action_required=True,

            alert_message=alert_message,

            extra_data=json.dumps(
                extra_data or {}
            )
        )


        # ------------------------------------------
        # SAVE EVENT
        # ------------------------------------------

        db.add(event)

        db.commit()

        db.refresh(event)


        print(
            f"Event created: "
            f"{event.event_id} | "
            f"{event.event_type} | "
            f"priority={event.priority}"
        )


        return event


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()