from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from datetime import datetime

import sys
import os

# Allow importing database.py from the project database folder
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

sys.path.insert(
    0,
    os.path.join(PROJECT_ROOT, "database")
)

from database import Base


class Event(Base):

    __tablename__ = "events"

    # ---------------------------------------------
    # PRIMARY IDENTIFICATION
    # ---------------------------------------------

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    event_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    # ---------------------------------------------
    # EVENT INFORMATION
    # ---------------------------------------------

    event_type = Column(
        String,
        nullable=False,
        index=True
    )

    confidence = Column(
        Float,
        nullable=False
    )

    severity = Column(
        String,
        nullable=False
    )

    priority = Column(
        Integer,
        nullable=False
    )

    # ---------------------------------------------
    # BUS INFORMATION
    # ---------------------------------------------

    bus_id = Column(
        String,
        nullable=False,
        index=True
    )

    # ---------------------------------------------
    # VIDEO INFORMATION
    # ---------------------------------------------

    video_timestamp = Column(
        Float,
        nullable=False
    )

    # ---------------------------------------------
    # GPS INFORMATION
    # ---------------------------------------------

    latitude = Column(
        Float,
        nullable=False
    )

    longitude = Column(
        Float,
        nullable=False
    )

    # ---------------------------------------------
    # EVENT STATUS
    # ---------------------------------------------

    status = Column(
        String,
        default="NEW"
    )

    action_required = Column(
        Boolean,
        default=False
    )

    alert_message = Column(
        String
    )

    # ---------------------------------------------
    # EVIDENCE
    # ---------------------------------------------

    evidence_image = Column(
        String
    )

    # ---------------------------------------------
    # ADDITIONAL DATA
    # ---------------------------------------------

    extra_data = Column(
        JSON,
        default=dict
    )

    # ---------------------------------------------
    # DETECTION TIME
    # ---------------------------------------------

    detected_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):

        return (
            f"<Event("
            f"event_id={self.event_id}, "
            f"type={self.event_type}, "
            f"priority={self.priority}"
            f")>"
        )