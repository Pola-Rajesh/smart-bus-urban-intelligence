import json
import os


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = r"C:\Projects\smart-bus-urban-intelligence"

EVIDENCE_DIR = os.path.join(
    PROJECT_ROOT,
    "evidence"
)

POTHOLE_JSON = os.path.join(
    EVIDENCE_DIR,
    "pothole_events.json"
)

WATERLOGGING_JSON = os.path.join(
    EVIDENCE_DIR,
    "waterlogging_events.json"
)

OUTPUT_JSON = os.path.join(
    EVIDENCE_DIR,
    "unified_events.json"
)


# ============================================================
# LOAD EVENTS
# ============================================================

def load_events(filename):

    if not os.path.exists(filename):
        print()
        print("WARNING: File not found:")
        print(filename)
        return []

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(
            f"Expected a list of events in {filename}"
        )

    return data


# ============================================================
# ADD UNIQUE EVENT IDS
# ============================================================

def assign_event_ids(events):

    for index, event in enumerate(events, start=1):

        event["event_id"] = (
            f"EVT-{index:04d}"
        )

    return events


# ============================================================
# MAIN AGGREGATION
# ============================================================

print()
print("============================================")
print(" SMART BUS EVENT AGGREGATOR")
print("============================================")


print()
print("Loading pothole events...")

pothole_events = load_events(
    POTHOLE_JSON
)

print(
    f"Pothole events loaded: "
    f"{len(pothole_events)}"
)


print()
print("Loading waterlogging events...")

waterlogging_events = load_events(
    WATERLOGGING_JSON
)

print(
    f"Waterlogging events loaded: "
    f"{len(waterlogging_events)}"
)


# ============================================================
# COMBINE EVENTS
# ============================================================

all_events = (
    pothole_events
    + waterlogging_events
)


# ============================================================
# SORT BY VIDEO TIMESTAMP
# ============================================================

all_events.sort(
    key=lambda event:
    float(event.get("video_timestamp", 0))
)


# ============================================================
# ASSIGN EVENT IDS
# ============================================================

all_events = assign_event_ids(
    all_events
)


# ============================================================
# SAVE UNIFIED EVENTS
# ============================================================

with open(
    OUTPUT_JSON,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        all_events,
        f,
        indent=4
    )


# ============================================================
# SUMMARY
# ============================================================

print()
print("============================================")
print(" AGGREGATION COMPLETE")
print("============================================")

print(
    f"Total events: {len(all_events)}"
)

print(
    f"Pothole events: {len(pothole_events)}"
)

print(
    f"Waterlogging events: "
    f"{len(waterlogging_events)}"
)

print()
print("Unified event order:")

for event in all_events:

    print(
        f"{event['event_id']} | "
        f"{event['event_type']} | "
        f"{event['video_timestamp']:.2f}s | "
        f"{event['confidence']:.3f}"
    )

print()
print("Output:")
print(OUTPUT_JSON)

print("============================================")