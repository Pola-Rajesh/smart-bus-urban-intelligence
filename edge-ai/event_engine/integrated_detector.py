import sys
import os
import json
import cv2
from datetime import datetime

from ultralytics import YOLO

# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = r"C:\Projects\smart-bus-urban-intelligence"

MODEL_PATH = (
    PROJECT_ROOT
    + r"\edge-ai\number_plate\Auto-Num-Plate-Recognition"
    + r"\runs\detect\train-3\weights\best.pt"
)

VIDEO_PATH = (
    PROJECT_ROOT
    + r"\datasets\road_damage\archive\videos_without_audio"
    + r"\10th July-20231125T045234Z-001\10th July\66_10-07-2023.mp4"
)

GPS_PATH = PROJECT_ROOT + r"\gps\tracks"

GPS_FILE = GPS_PATH + r"\bus_07_track.csv"

EVIDENCE_DIR = PROJECT_ROOT + r"\evidence\waterlogging"

OUTPUT_JSON = PROJECT_ROOT + r"\evidence\waterlogging_events.json"

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

MAX_VIDEO_SECONDS = 60

EVIDENCE_INTERVAL = 5

# ============================================================
# PREPARE FOLDERS
# ============================================================

os.makedirs(EVIDENCE_DIR, exist_ok=True)

# ============================================================
# LOAD MODEL + GPS
# ============================================================

print("Loading waterlogging model...")

model = YOLO(MODEL_PATH)

print("Loading GPS track...")

gps_track = load_gps_track(GPS_FILE)

# ============================================================
# OPEN VIDEO
# ============================================================

print("Opening video...")

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    raise RuntimeError("Could not open video")

fps = cap.get(cv2.CAP_PROP_FPS)

if fps <= 0:
    raise RuntimeError("Could not determine video FPS")

total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

video_duration = total_frames / fps

processing_duration = min(
    video_duration,
    MAX_VIDEO_SECONDS
)

print()
print("============================================")
print(" SMART BUS WATERLOGGING DETECTOR")
print("============================================")
print(f"FPS: {fps:.2f}")
print(f"Video duration: {video_duration:.2f} sec")
print(f"Processing: {processing_duration:.2f} sec")
print("============================================")
print()

# ============================================================
# PROCESS VIDEO
# ============================================================

events = []

frame_number = 0

last_evidence_time = -999

while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame_number += 1

    video_timestamp = frame_number / fps

    # Stop after our GPS coverage
    if video_timestamp > processing_duration:
        break

    # --------------------------------------------------------
    # YOLO DETECTION
    # --------------------------------------------------------

    results = model.predict(
        frame,
        conf=CONFIDENCE_THRESHOLD,
        verbose=False
    )

    result = results[0]

    detection_found = False
    best_confidence = 0.0
    best_box = None

    if result.boxes is not None:

        for box in result.boxes:

            confidence = float(box.conf[0])

            if confidence > best_confidence:

                best_confidence = confidence

                best_box = box.xyxy[0].cpu().numpy()

                detection_found = True

    # --------------------------------------------------------
    # CREATE EVENT
    # --------------------------------------------------------

    if detection_found:

        # Avoid generating an event every single frame
        if video_timestamp - last_evidence_time >= EVIDENCE_INTERVAL:

            location = get_location(
                video_timestamp,
                gps_track
            )

            # ----------------------------------------------
            # DRAW EVIDENCE IMAGE
            # ----------------------------------------------

            evidence_frame = frame.copy()

            x1, y1, x2, y2 = map(
                int,
                best_box
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
                f"{best_confidence:.0%}"
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

            # ----------------------------------------------
            # SAVE IMAGE
            # ----------------------------------------------

            filename = (
                f"waterlogging_"
                f"{video_timestamp:.1f}s.jpg"
            )

            evidence_path = os.path.join(
                EVIDENCE_DIR,
                filename
            )

            cv2.imwrite(
                evidence_path,
                evidence_frame
            )

            # ----------------------------------------------
            # CREATE SMART BUS EVENT
            # ----------------------------------------------

            event = create_event(

                event_type="waterlogging",

                confidence=best_confidence,

                bus_id=location["bus_id"],

                video_timestamp=video_timestamp,

                latitude=location["latitude"],

                longitude=location["longitude"],

                severity="HIGH",

                evidence_image=evidence_path

            )

            events.append(event)

            last_evidence_time = video_timestamp

            print()
            print("🚨 WATERLOGGING EVENT")

            print(
                f"Time: {video_timestamp:.1f}s"
            )

            print(
                f"Confidence: "
                f"{best_confidence:.2%}"
            )

            print(
                f"Bus: "
                f"{location['bus_id']}"
            )

            print(
                f"GPS: "
                f"{location['latitude']:.6f}, "
                f"{location['longitude']:.6f}"
            )

            print(
                f"Evidence: "
                f"{evidence_path}"
            )

# ============================================================
# CLEAN UP
# ============================================================

cap.release()

# ============================================================
# SAVE EVENTS
# ============================================================

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

print()
print("============================================")
print(" PROCESSING COMPLETE")
print("============================================")

print(
    f"Total events: {len(events)}"
)

print(
    f"Evidence folder: {EVIDENCE_DIR}"
)

print(
    f"Events JSON: {OUTPUT_JSON}"
)

print("============================================")