import sys
from pathlib import Path
from datetime import datetime

# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ============================================================
# EDGE AI VIDEO PROCESSOR
# ============================================================

VIDEO_PROCESSOR_DIR = (
    PROJECT_ROOT
    / "edge-ai"
    / "video_processor"
)

if str(VIDEO_PROCESSOR_DIR) not in sys.path:
    sys.path.insert(0, str(VIDEO_PROCESSOR_DIR))

from video_processor import process_video

# ============================================================
# DATABASE
# ============================================================

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.database import SessionLocal
from database.models import ProcessingSession

# ============================================================
# DATABASE EVENT INGESTION
# ============================================================

BACKEND_SERVICES_DIR = (
    PROJECT_ROOT
    / "backend"
    / "services"
)

if str(BACKEND_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_SERVICES_DIR))

from event_ingestion import create_event


# ============================================================
# CREATE SESSION ID
# ============================================================

def generate_session_id():

    now = datetime.now()

    return (
        f"SESSION-"
        f"{now.strftime('%Y%m%d')}-"
        f"{now.strftime('%H%M%S')}"
    )


# ============================================================
# PROCESS UPLOADED VIDEO
# ============================================================

def process_uploaded_video(video_path):

    video_path = Path(video_path)

    if not video_path.exists():

        raise FileNotFoundError(
            f"Video not found: {video_path}"
        )

    print()
    print("============================================")
    print(" SMART BUS VIDEO SERVICE")
    print("============================================")
    print(f"Processing: {video_path}")
    print()

    # ========================================================
    # CREATE PROCESSING SESSION
    # ========================================================

    session_id = generate_session_id()

    db = SessionLocal()

    session = ProcessingSession(

        session_id=session_id,

        video_filename=video_path.name,

        uploaded_at=datetime.now(),

        status="PROCESSING",

        total_events=0
    )

    db.add(session)

    db.commit()

    db.refresh(session)

    db.close()

    print(
        f"Processing session created: "
        f"{session_id}"
    )

    # ========================================================
    # RUN EDGE AI
    # ========================================================

    try:

        detected_events = process_video(
            video_path
        )

    except Exception:

        db = SessionLocal()

        failed_session = (
            db.query(ProcessingSession)
            .filter(
                ProcessingSession.session_id
                == session_id
            )
            .first()
        )

        if failed_session:

            failed_session.status = "FAILED"
            failed_session.completed_at = datetime.now()

            db.commit()

        db.close()

        raise

    # ========================================================
    # STORE EVENTS
    # ========================================================

    database_events = []

    for detected in detected_events:

        event = create_event(

            event_type=detected["event_type"],

            confidence=detected["confidence"],

            bus_id=detected["bus_id"],

            video_timestamp=detected["video_timestamp"],

            latitude=detected["latitude"],

            longitude=detected["longitude"],

            evidence_image=detected["evidence_image"],

            extra_data=detected.get(
                "extra_data",
                {}
            ),

            # IMPORTANT:
            # Attach event to this processing session
            session_id=session_id
        )

        database_events.append(event)

    # ========================================================
    # COMPLETE SESSION
    # ========================================================

    db = SessionLocal()

    completed_session = (
        db.query(ProcessingSession)
        .filter(
            ProcessingSession.session_id
            == session_id
        )
        .first()
    )

    if completed_session:

        completed_session.status = "COMPLETED"

        completed_session.completed_at = datetime.now()

        completed_session.total_events = (
            len(database_events)
        )

        db.commit()

    db.close()

    # ========================================================
    # RESULT
    # ========================================================

    print()
    print("============================================")
    print(" VIDEO SERVICE COMPLETE")
    print("============================================")

    print(
        f"Session: {session_id}"
    )

    print(
        f"AI detections: "
        f"{len(detected_events)}"
    )

    print(
        f"Database events: "
        f"{len(database_events)}"
    )

    print("============================================")

    return database_events
