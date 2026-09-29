import sys
import os
import json
import cv2

from ultralytics import YOLO

# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = r"C:\Projects\smart-bus-urban-intelligence"

MODEL_PATH = (
    PROJECT_ROOT
    + r"\models\waterlogging\waterlogging_yolo11n"
    + r"\weights\best.pt"
)

VIDEO_PATH = (
    PROJECT_ROOT
    + r"\datasets\waterlogging_test\waterlogging_test.mp4"
)

GPS_PATH = PROJECT_ROOT + r"\gps\tracks"
GPS_FILE = GPS_PATH + r"\bus_07_track.csv"

EVIDENCE_DIR = (
    PROJECT_ROOT
    + r"\evidence\waterlogging"
)

OUTPUT_JSON = (
    PROJECT_ROOT
    + r"\evidence\waterlogging_events.json"
)

# ============================================================
# GPS MODULE
# ============================================================

sys.path.insert(0, GPS_PATH)

from gps_lookup import load_gps_track, get_location

# ============================================================
# EVENT ENGINE
# ============================================================

sys.path.insert(
    0,
    PROJECT_ROOT + r"\edge-ai\event_engine"
)

from event_engine import create_event

# ============================================================
# SETTINGS
# ============================================================

CONFIDENCE_THRESHOLD = 0.25

MIN_EVENT_CONFIDENCE = 0.35

MAX_VIDEO_SECONDS = 120

# Frames separated by more than this are treated
# as different temporal events.

MAX_GAP_SECONDS = 1.0

# ============================================================
# PREPARE FOLDERS
# ============================================================

os.makedirs(EVIDENCE_DIR, exist_ok=True)

# ============================================================
# LOAD MODEL + GPS
# ============================================================

print()
print("============================================")
print(" SMART BUS WATERLOGGING EVENT DETECTOR")
print("============================================")

print()
print("Loading waterlogging model...")

model = YOLO(MODEL_PATH)

print("Model loaded successfully.")

print("Loading GPS track...")

gps_track = load_gps_track(GPS_FILE)

print("GPS track loaded successfully.")

# ============================================================
# OPEN VIDEO
# ============================================================

print("Opening video...")

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    raise RuntimeError(
        f"Could not open video:\n{VIDEO_PATH}"
    )

fps = cap.get(cv2.CAP_PROP_FPS)

if fps <= 0:
    raise RuntimeError(
        "Could not determine video FPS."
    )

total_frames = int(
    cap.get(cv2.CAP_PROP_FRAME_COUNT)
)

video_duration = total_frames / fps

processing_duration = min(
    video_duration,
    MAX_VIDEO_SECONDS
)

print()
print("--------------------------------------------")
print(f"FPS: {fps:.2f}")
print(f"Total frames: {total_frames}")
print(f"Video duration: {video_duration:.2f} sec")
print(f"Processing: {processing_duration:.2f} sec")
print("--------------------------------------------")

# ============================================================
# FRAME DETECTION STORAGE
# ============================================================

detections = []

frame_number = 0

while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame_number += 1

    video_timestamp = (
        frame_number / fps
    )

    if video_timestamp > processing_duration:
        break

    results = model.predict(
        frame,
        conf=CONFIDENCE_THRESHOLD,
        verbose=False
    )

    result = results[0]

    if result.boxes is None:
        continue

    best_confidence = 0.0
    best_box = None

    for box in result.boxes:

        confidence = float(
            box.conf[0]
        )

        if confidence > best_confidence:

            best_confidence = confidence

            best_box = (
                box.xyxy[0]
                .cpu()
                .numpy()
            )

    if best_box is not None:

        detections.append({
            "frame": frame_number,
            "timestamp": video_timestamp,
            "confidence": best_confidence,
            "box": best_box.tolist(),
            "frame_image": frame.copy()
        })


cap.release()

# ============================================================
# DETECTION SUMMARY
# ============================================================

print()
print("============================================")
print(" DETECTION SUMMARY")
print("============================================")

print(
    f"Frames processed: {frame_number}"
)

print(
    f"Frames containing waterlogging: "
    f"{len(detections)}"
)

# ============================================================
# TEMPORAL GROUPING
# ============================================================

groups = []

current_group = []

for detection in detections:

    if not current_group:

        current_group = [detection]

        continue

    gap = (
        detection["timestamp"]
        - current_group[-1]["timestamp"]
    )

    if gap <= MAX_GAP_SECONDS:

        current_group.append(
            detection
        )

    else:

        groups.append(
            current_group
        )

        current_group = [detection]


if current_group:

    groups.append(
        current_group
    )

# ============================================================
# FILTER GROUPS
# ============================================================

valid_groups = []

for group in groups:

    best = max(
        group,
        key=lambda x: x["confidence"]
    )

    if (
        best["confidence"]
        >= MIN_EVENT_CONFIDENCE
    ):

        valid_groups.append(
            group
        )

# ============================================================
# GROUP SUMMARY
# ============================================================

print()
print("============================================")
print(" TEMPORAL WATERLOGGING GROUPS")
print("============================================")

for index, group in enumerate(
    valid_groups,
    start=1
):

    best = max(
        group,
        key=lambda x: x["confidence"]
    )

    print(
        f"Group #{index}: "
        f"frames "
        f"{group[0]['frame']}-"
        f"{group[-1]['frame']} | "
        f"{group[0]['timestamp']:.2f}-"
        f"{group[-1]['timestamp']:.2f}s | "
        f"detections={len(group)} | "
        f"best={best['confidence']:.3f}"
    )

# ============================================================
# CREATE EVENTS
# ============================================================

events = []

for event_number, group in enumerate(
    valid_groups,
    start=1
):

    best = max(
        group,
        key=lambda x: x["confidence"]
    )

    timestamp = best["timestamp"]

    location = get_location(
        timestamp,
        gps_track
    )

    evidence_frame = (
        best["frame_image"].copy()
    )

    x1, y1, x2, y2 = map(
        int,
        best["box"]
    )

    cv2.rectangle(
        evidence_frame,
        (x1, y1),
        (x2, y2),
        (0, 0, 255),
        3
    )

    label = (
        f"Waterlogging "
        f"{best['confidence']:.1%}"
    )

    cv2.putText(
        evidence_frame,
        label,
        (x1, max(y1 - 10, 30)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 255),
        2
    )

    filename = (
        f"waterlogging_"
        f"{event_number}_"
        f"{timestamp:.2f}s.jpg"
    )

    evidence_path = os.path.join(
        EVIDENCE_DIR,
        filename
    )

    cv2.imwrite(
        evidence_path,
        evidence_frame
    )

    event = create_event(

        event_type="waterlogging",

        confidence=best["confidence"],

        bus_id=location["bus_id"],

        video_timestamp=timestamp,

        latitude=location["latitude"],

        longitude=location["longitude"],

        severity="HIGH",

        evidence_image=evidence_path,

        extra_data={
            "frame": best["frame"],
            "group_frames": len(group)
        }
    )

    events.append(event)

    print()
    print("💧 WATERLOGGING EVENT")
    print("--------------------------------------------")

    print(
        f"Event: {event_number}"
    )

    print(
        f"Frame: {best['frame']}"
    )

    print(
        f"Time: {timestamp:.2f}s"
    )

    print(
        f"Confidence: "
        f"{best['confidence']:.2%}"
    )

    print(
        f"Bus: {location['bus_id']}"
    )

    print(
        f"GPS: "
        f"{location['latitude']:.6f}, "
        f"{location['longitude']:.6f}"
    )

    print(
        f"Evidence: {evidence_path}"
    )

# ============================================================
# SAVE EVENTS
# ============================================================

os.makedirs(
    os.path.dirname(OUTPUT_JSON),
    exist_ok=True
)

with open(
    OUTPUT_JSON,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        events,
        f,
        indent=4
    )

# ============================================================
# COMPLETE
# ============================================================

print()
print("============================================")
print(" WATERLOGGING PROCESSING COMPLETE")
print("============================================")

print(
    f"Total temporal groups: "
    f"{len(valid_groups)}"
)

print(
    f"Total waterlogging events: "
    f"{len(events)}"
)

print(
    f"Evidence folder:"
)

print(EVIDENCE_DIR)

print()
print("Events JSON:")

print(OUTPUT_JSON)

print("============================================")