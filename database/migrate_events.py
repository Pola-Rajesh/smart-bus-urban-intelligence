import json
import os
import sys

# --------------------------------------------------
# DATABASE IMPORT
# --------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.insert(0, BASE_DIR)

from database import SessionLocal
from models import Event


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

EVENTS_FILE = os.path.join(
    BASE_DIR,
    "evidence",
    "processed_events.json"
)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

print("============================================")
print(" SMART BUS EVENT MIGRATION")
print("============================================")
print()

# --------------------------------------------------
# LOAD EVENTS
# --------------------------------------------------

print("Loading processed events...")

with open(EVENTS_FILE, "r", encoding="utf-8") as file:
    data = json.load(file)


events = data.get("events", [])

print(f"Events found: {len(events)}")
print()


# --------------------------------------------------
# VALIDATE FORMAT
# --------------------------------------------------

if not isinstance(events, list):

    raise RuntimeError(
        "Invalid processed_events.json: "
        "'events' must be a list."
    )


if not events:

    print("No events found.")
    sys.exit(0)


# --------------------------------------------------
# DATABASE SESSION
# --------------------------------------------------

db = SessionLocal()


# --------------------------------------------------
# MIGRATE EVENTS
# --------------------------------------------------

print("Migrating events...")
print()

migrated = 0
skipped = 0


try:

    for event in events:

        if not isinstance(event, dict):

            print("Skipping invalid event record.")
            skipped += 1
            continue


        event_id = event.get("event_id")

        if not event_id:

            print("Skipping event without event_id.")
            skipped += 1
            continue


        # ------------------------------------------
        # CHECK DUPLICATE
        # ------------------------------------------

        existing = (
            db.query(Event)
            .filter(Event.event_id == event_id)
            .first()
        )

        if existing:

            print(
                f"Skipping existing event: {event_id}"
            )

            skipped += 1
            continue


        # ------------------------------------------
        # CREATE EVENT
        # ------------------------------------------

        new_event = Event(

            event_id=event.get("event_id"),

            event_type=event.get("event_type"),

            confidence=event.get("confidence"),

            bus_id=event.get("bus_id"),

            video_timestamp=event.get("video_timestamp"),

            latitude=event.get("latitude"),

            longitude=event.get("longitude"),

            severity=event.get("severity"),

            detected_at=event.get("detected_at"),

            evidence_image=event.get("evidence_image"),

            priority=event.get("priority"),

            status=event.get("status"),

            action_required=event.get(
                "action_required",
                False
            ),

            alert_message=event.get("alert_message"),

            extra_data=json.dumps(
                event.get("extra_data", {})
            )
        )


        db.add(new_event)

        migrated += 1


        print(
            f"Migrated: {event_id} | "
            f"{event.get('event_type')} | "
            f"priority={event.get('priority')}"
        )


    # ------------------------------------------
    # COMMIT
    # ------------------------------------------

    db.commit()


except Exception as error:

    db.rollback()

    print()
    print("ERROR DURING MIGRATION")
    print("--------------------------------------------")
    print(error)

    sys.exit(1)


finally:

    db.close()


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

print()

print("============================================")
print(" EVENT MIGRATION COMPLETE")
print("============================================")

print(f"Events found:       {len(events)}")
print(f"Events migrated:    {migrated}")
print(f"Events skipped:     {skipped}")

print()

print("Database:")

print(
    os.path.join(
        BASE_DIR,
        "database",
        "smart_bus.db"
    )
)

print("============================================")