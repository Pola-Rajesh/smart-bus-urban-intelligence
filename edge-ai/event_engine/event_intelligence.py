import os
import json


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = r"C:\Projects\smart-bus-urban-intelligence"

INPUT_JSON = os.path.join(
    PROJECT_ROOT,
    "evidence",
    "unified_events.json"
)

OUTPUT_JSON = os.path.join(
    PROJECT_ROOT,
    "evidence",
    "processed_events.json"
)


# ============================================================
# CONFIGURATION
# ============================================================

# Minimum confidence required for an event
MIN_CONFIDENCE = 0.40


# ============================================================
# SEVERITY LOGIC
# ============================================================

def calculate_severity(event):

    event_type = event.get("event_type")
    confidence = float(event.get("confidence", 0))

    # --------------------------------------------------------
    # POTHOLE
    # --------------------------------------------------------

    if event_type == "pothole":

        if confidence >= 0.70:
            return "HIGH"

        elif confidence >= 0.50:
            return "MEDIUM"

        else:
            return "LOW"

    # --------------------------------------------------------
    # WATERLOGGING
    # --------------------------------------------------------

    elif event_type == "waterlogging":

        if confidence >= 0.65:
            return "HIGH"

        elif confidence >= 0.45:
            return "MEDIUM"

        else:
            return "LOW"

    # --------------------------------------------------------
    # TRAFFIC
    # --------------------------------------------------------

    elif event_type == "traffic":

        traffic_level = (
            event.get("extra_data", {})
            .get("traffic_level", "")
            .upper()
        )

        if traffic_level == "HIGH":
            return "HIGH"

        elif traffic_level == "MEDIUM":
            return "MEDIUM"

        else:
            return "LOW"

    return "MEDIUM"


# ============================================================
# EVENT PRIORITY
# ============================================================

def calculate_priority(severity):

    if severity == "HIGH":
        return 3

    elif severity == "MEDIUM":
        return 2

    return 1


# ============================================================
# EVENT PROCESSING
# ============================================================

def process_event(event):

    confidence = float(
        event.get("confidence", 0)
    )

    # --------------------------------------------------------
    # IGNORE VERY LOW CONFIDENCE EVENTS
    # --------------------------------------------------------

    if confidence < MIN_CONFIDENCE:

        return None

    # --------------------------------------------------------
    # CALCULATE SEVERITY
    # --------------------------------------------------------

    severity = calculate_severity(event)

    # --------------------------------------------------------
    # CALCULATE PRIORITY
    # --------------------------------------------------------

    priority = calculate_priority(severity)

    # --------------------------------------------------------
    # ADD INTELLIGENCE FIELDS
    # --------------------------------------------------------

    event["severity"] = severity

    event["priority"] = priority

    event["status"] = "NEW"

    event["action_required"] = (
        severity in ["HIGH", "MEDIUM"]
    )

    # --------------------------------------------------------
    # HUMAN-READABLE MESSAGE
    # --------------------------------------------------------

    event_type = event.get(
        "event_type",
        "unknown"
    )

    if event_type == "pothole":

        event["alert_message"] = (
            "Road pothole detected"
        )

    elif event_type == "waterlogging":

        event["alert_message"] = (
            "Waterlogging detected on road"
        )

    elif event_type == "traffic":

        event["alert_message"] = (
            "Traffic congestion detected"
        )

    else:

        event["alert_message"] = (
            "Urban road event detected"
        )

    return event


# ============================================================
# LOAD UNIFIED EVENTS
# ============================================================

print()
print("============================================")
print(" SMART BUS EVENT INTELLIGENCE ENGINE")
print("============================================")
print()

print("Loading unified events...")

if not os.path.exists(INPUT_JSON):

    raise FileNotFoundError(
        f"Unified events file not found:\n"
        f"{INPUT_JSON}"
    )

with open(
    INPUT_JSON,
    "r",
    encoding="utf-8"
) as f:

    data = json.load(f)


# ============================================================
# HANDLE AGGREGATOR FORMAT
# ============================================================

if isinstance(data, dict):

    events = data.get(
        "events",
        []
    )

else:

    events = data


print(
    f"Events loaded: {len(events)}"
)


# ============================================================
# PROCESS EVENTS
# ============================================================

processed_events = []

filtered_events = 0

for event in events:

    processed_event = process_event(
        event
    )

    if processed_event is None:

        filtered_events += 1

        continue

    processed_events.append(
        processed_event
    )


# ============================================================
# SORT BY PRIORITY
# ============================================================

processed_events.sort(
    key=lambda event: (
        -event.get("priority", 0),
        event.get("video_timestamp", 0)
    )
)


# ============================================================
# SUMMARY
# ============================================================

summary = {

    "total_input_events":
        len(events),

    "total_processed_events":
        len(processed_events),

    "filtered_events":
        filtered_events,

    "high_priority":
        sum(
            1
            for e in processed_events
            if e.get("priority") == 3
        ),

    "medium_priority":
        sum(
            1
            for e in processed_events
            if e.get("priority") == 2
        ),

    "low_priority":
        sum(
            1
            for e in processed_events
            if e.get("priority") == 1
        )
}


# ============================================================
# OUTPUT
# ============================================================

output = {

    "system": "Smart Bus Urban Intelligence",

    "summary": summary,

    "events": processed_events
}


# ============================================================
# SAVE
# ============================================================

with open(
    OUTPUT_JSON,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        output,
        f,
        indent=4
    )


# ============================================================
# DISPLAY RESULTS
# ============================================================

print()
print("============================================")
print(" INTELLIGENCE PROCESSING COMPLETE")
print("============================================")

print(
    f"Input events: "
    f"{summary['total_input_events']}"
)

print(
    f"Processed events: "
    f"{summary['total_processed_events']}"
)

print(
    f"Filtered events: "
    f"{summary['filtered_events']}"
)

print()
print("Priority summary")
print("--------------------------------------------")

print(
    f"HIGH:   "
    f"{summary['high_priority']}"
)

print(
    f"MEDIUM: "
    f"{summary['medium_priority']}"
)

print(
    f"LOW:    "
    f"{summary['low_priority']}"
)

print()
print("Processed event timeline")
print("--------------------------------------------")

for event in processed_events:

    print(
        f"{event['event_id']} | "
        f"{event['event_type']} | "
        f"confidence="
        f"{event['confidence']:.3f} | "
        f"severity="
        f"{event['severity']} | "
        f"priority="
        f"{event['priority']} | "
        f"GPS="
        f"{event['latitude']:.6f}, "
        f"{event['longitude']:.6f}"
    )

print("--------------------------------------------")

print()
print(
    "Output JSON:"
)

print(OUTPUT_JSON)

print()
print("============================================")