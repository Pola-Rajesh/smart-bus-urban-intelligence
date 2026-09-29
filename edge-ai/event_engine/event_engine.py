from datetime import datetime


def create_event(
    event_type,
    confidence,
    bus_id,
    video_timestamp,
    latitude,
    longitude,
    severity="MEDIUM",
    evidence_image=None,
    extra_data=None
):
    """
    Create a standardized Smart Bus urban intelligence event.
    """

    event = {
        "event_type": event_type,
        "confidence": round(float(confidence), 3),
        "bus_id": bus_id,
        "video_timestamp": round(float(video_timestamp), 2),

        "latitude": round(float(latitude), 6),
        "longitude": round(float(longitude), 6),

        "severity": severity,

        "detected_at": datetime.now().isoformat(
            timespec="seconds"
        ),

        "evidence_image": evidence_image,

        "extra_data": extra_data or {}
    }

    return event


# ---------------------------------
# TEST EVENT
# ---------------------------------

if __name__ == "__main__":

    event = create_event(
        event_type="waterlogging",
        confidence=0.82,
        bus_id="BUS-07",
        video_timestamp=27,
        latitude=15.829620,
        longitude=78.038820,
        severity="HIGH",
        evidence_image="waterlogging_27s.jpg"
    )

    print("\n===== SMART BUS EVENT =====")

    for key, value in event.items():
        print(f"{key}: {value}")