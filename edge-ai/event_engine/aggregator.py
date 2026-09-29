import os
import json


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

TRAFFIC_JSON = os.path.join(
    EVIDENCE_DIR,
    "traffic_events.json"
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
        print(f"WARNING: File not found:")
        print(filename)
        return []

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    if not isinstance(data, list):
        print(f"WARNING: Invalid event format in {filename}")
        return []

    return data


# ============================================================
# LOAD ALL EVENT SOURCES
# ============================================================

print()
print("============================================")
print(" SMART BUS EVENT AGGREGATOR")
print("============================================")
print()

print("Loading pothole events...")
pothole_events = load_events(POTHOLE_JSON)
print(f"Pothole events loaded: {len(pothole_events)}")

print()

print("Loading waterlogging events...")
waterlogging_events = load_events(WATERLOGGING_JSON)
print(
    f"Waterlogging events loaded: "
    f"{len(waterlogging_events)}"
)

print()

print("Loading traffic events...")
traffic_events = load_events(TRAFFIC_JSON)
print(
    f"Traffic events loaded: "
    f"{len(traffic_events)}"
)


# ============================================================
# COMBINE EVENTS
# ============================================================

all_events = (
    pothole_events
    + waterlogging_events
    + traffic_events
)


# ============================================================
# SORT BY VIDEO TIMESTAMP
# ============================================================

all_events.sort(
    key=lambda event:
    float(event.get("video_timestamp", 0))
)


# ============================================================
# ASSIGN UNIQUE EVENT IDs
# ============================================================

for index, event in enumerate(
    all_events,
    start=1
):

    event["event_id"] = (
        f"EVT-{index:04d}"
    )


# ============================================================
# EVENT SUMMARY
# ============================================================

summary = {
    "total_events": len(all_events),
    "pothole_events": len(pothole_events),
    "waterlogging_events": len(waterlogging_events),
    "traffic_events": len(traffic_events)
}


# ============================================================
# CREATE UNIFIED OUTPUT
# ============================================================

output = {
    "summary": summary,
    "events": all_events
}


# ============================================================
# SAVE UNIFIED EVENTS
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
print(" EVENT AGGREGATION COMPLETE")
print("============================================")

print(
    f"Total events: "
    f"{len(all_events)}"
)

print(
    f"Pothole events: "
    f"{len(pothole_events)}"
)

print(
    f"Waterlogging events: "
    f"{len(waterlogging_events)}"
)

print(
    f"Traffic events: "
    f"{len(traffic_events)}"
)

print()
print("Unified event timeline:")
print("--------------------------------------------")

for event in all_events:

    print(
        f"{event['event_id']} | "
        f"{event['video_timestamp']:.2f}s | "
        f"{event['event_type']} | "
        f"GPS: "
        f"{event['latitude']:.6f}, "
        f"{event['longitude']:.6f}"
    )

print("--------------------------------------------")

print()
print(
    f"Output JSON:\n"
    f"{OUTPUT_JSON}"
)

print("============================================")