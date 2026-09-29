from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey
from database.database import Base


# ============================================================
# PROCESSING SESSION
# ============================================================

class ProcessingSession(Base):

    __tablename__ = "processing_sessions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    session_id = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    video_filename = Column(
        String,
        nullable=False
    )

    uploaded_at = Column(
        String
    )

    completed_at = Column(
        String
    )

    status = Column(
        String
    )

    total_events = Column(
        Integer,
        default=0
    )


# ============================================================
# EVENT
# ============================================================

class Event(Base):

    __tablename__ = "events"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    event_id = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    # --------------------------------------------------------
    # PROCESSING SESSION
    # --------------------------------------------------------

    session_id = Column(
        String,
        ForeignKey(
            "processing_sessions.session_id"
        ),
        nullable=True,
        index=True
    )

    event_type = Column(
        String,
        nullable=False
    )

    confidence = Column(
        Float
    )

    bus_id = Column(
        String
    )

    video_timestamp = Column(
        Float
    )

    latitude = Column(
        Float
    )

    longitude = Column(
        Float
    )

    severity = Column(
        String
    )

    detected_at = Column(
        String
    )

    evidence_image = Column(
        String
    )

    priority = Column(
        Integer
    )

    status = Column(
        String
    )

    action_required = Column(
        Boolean
    )

    alert_message = Column(
        String
    )

    extra_data = Column(
        Text
    )