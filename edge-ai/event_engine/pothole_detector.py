import sys
import os
import json
import cv2

from ultralytics import YOLO


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = r"C:\Projects\smart-bus-urban-intelligence"

MODEL_PATH = (
    PROJECT_ROOT
    + r"\models\road_damage\pothole_v2_yolo11n\weights\best.pt"
)

VIDEO_PATH = (
    PROJECT_ROOT
    + r"\datasets\road_damage\archive\videos_without_audio"
    + r"\10th July-20231125T045234Z-001\10th July\66_10-07-2023.mp4"
)

GPS_PATH = PROJECT_ROOT + r"\gps\tracks"

GPS_FILE = GPS_PATH + r"\bus_07_track.csv"


EVIDENCE_DIR = (
    PROJECT_ROOT
    + r"\evidence\pothole"
)

OUTPUT_JSON = (
    PROJECT_ROOT
    + r"\evidence\pothole_events.json"
)


# ============================================================
# IMPORT GPS MODULE
# ============================================================

from gps_provider import ReplayGPSProvider

# ============================================================
# IMPORT EVENT ENGINE
# ============================================================

sys.path.insert(
    0,
    PROJECT_ROOT + r"\edge-ai\event_engine"
)

from event_engine import create_event


# ============================================================
# SETTINGS
# ============================================================

CONFIDENCE_THRESHOLD = 0.50

MAX_VIDEO_SECONDS = 60

# Maximum frame gap allowed inside one temporal group.
TEMPORAL_GAP = 3


# ============================================================
# PREPARE OUTPUT FOLDER
# ============================================================

os.makedirs(EVIDENCE_DIR, exist_ok=True)


# ============================================================
# LOAD MODEL
# ============================================================

print()
print("============================================")
print(" SMART BUS POTHOLE DETECTOR")
print("============================================")
print()

print("Loading pothole model...")

model = YOLO(MODEL_PATH)

print("Model loaded successfully.")


# ============================================================
# LOAD GPS
# ============================================================

print("Loading GPS track...")

gps_provider = ReplayGPSProvider(GPS_FILE)

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
print()


# ============================================================
# FIRST PASS
# COLLECT POTHOLE DETECTIONS
# ============================================================

detections = []

frame_number = 0


while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame_number += 1

    video_timestamp = frame_number / fps

    if video_timestamp > processing_duration:
        break


    # --------------------------------------------------------
    # YOLO
    # --------------------------------------------------------

    results = model.predict(
        frame,
        conf=CONFIDENCE_THRESHOLD,
        verbose=False
    )

    result = results[0]


    if result.boxes is None:
        continue


    for box in result.boxes:

        class_id = int(box.cls[0])

        confidence = float(
            box.conf[0]
        )


        # ----------------------------------------------------
        # IMPORTANT:
        # Our model classes are:
        #
        # 0 = crocodile crack
        # 1 = longitudinal crack
        # 2 = pothole
        # ----------------------------------------------------

        class_name = model.names[class_id]

        if class_name.lower() != "pothole":
            continue


        x1, y1, x2, y2 = (
            box.xyxy[0]
            .cpu()
            .numpy()
        )


        detections.append(
            {
                "frame": frame_number,
                "timestamp": video_timestamp,
                "confidence": confidence,
                "x1": float(x1),
                "y1": float(y1),
                "x2": float(x2),
                "y2": float(y2)
            }
        )


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
    f"Pothole detections: {len(detections)}"
)

frames_with_detections = sorted(
    set(
        d["frame"]
        for d in detections
    )
)

print(
    f"Frames containing potholes: "
    f"{len(frames_with_detections)}"
)

print("============================================")
print()


if not detections:

    print(
        "No potholes detected above "
        f"confidence {CONFIDENCE_THRESHOLD:.2f}"
    )

    with open(
        OUTPUT_JSON,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            [],
            f,
            indent=4
        )

    raise SystemExit


# ============================================================
# TEMPORAL GROUPING
# ============================================================

groups = []

current_group = []


for frame in frames_with_detections:

    if not current_group:

        current_group = [frame]

        continue


    previous_frame = current_group[-1]


    if frame - previous_frame <= TEMPORAL_GAP:

        current_group.append(frame)

    else:

        groups.append(
            current_group
        )

        current_group = [frame]


if current_group:

    groups.append(
        current_group
    )


# ============================================================
# GROUP SUMMARY
# ============================================================

print("============================================")
print(" TEMPORAL POTHOLE GROUPS")
print("============================================")


for index, group in enumerate(
    groups,
    start=1
):

    start_frame = group[0]

    end_frame = group[-1]

    start_time = start_frame / fps

    end_time = end_frame / fps


    group_detections = [
        d
        for d in detections
        if d["frame"] in group
    ]


    best = max(
        group_detections,
        key=lambda d: d["confidence"]
    )


    print(
        f"Group #{index}: "
        f"frames {start_frame}-{end_frame} | "
        f"{start_time:.2f}-{end_time:.2f}s | "
        f"detections={len(group_detections)} | "
        f"best={best['confidence']:.3f}"
    )


print("============================================")
print()


# ============================================================
# CREATE EVENTS
# ============================================================

events = []


for index, group in enumerate(
    groups,
    start=1
):


    group_detections = [
        d
        for d in detections
        if d["frame"] in group
    ]


    # --------------------------------------------------------
    # Select strongest detection
    # --------------------------------------------------------

    best = max(
        group_detections,
        key=lambda d: d["confidence"]
    )


    frame_number = best["frame"]

    timestamp = best["timestamp"]


    # --------------------------------------------------------
    # GET GPS LOCATION
    # --------------------------------------------------------

    
    location = gps_provider.get_location(
    timestamp
	)


    # --------------------------------------------------------
    # REOPEN VIDEO AND EXTRACT BEST FRAME
    # --------------------------------------------------------

    cap = cv2.VideoCapture(
        VIDEO_PATH
    )

    cap.set(
        cv2.CAP_PROP_POS_FRAMES,
        frame_number - 1
    )

    success, frame = cap.read()

    cap.release()


    if not success:

        print(
            f"WARNING: Could not extract "
            f"frame {frame_number}"
        )

        continue


    # --------------------------------------------------------
    # DRAW BOUNDING BOX
    # --------------------------------------------------------

    x1 = int(best["x1"])
    y1 = int(best["y1"])
    x2 = int(best["x2"])
    y2 = int(best["y2"])


    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        (0, 0, 255),
        3
    )


    label = (
        f"Pothole "
        f"{best['confidence']:.0%}"
    )


    cv2.putText(
        frame,
        label,
        (x1, max(y1 - 10, 30)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 255),
        2
    )


    # --------------------------------------------------------
    # SAVE EVIDENCE IMAGE
    # --------------------------------------------------------

    filename = (
        f"pothole_"
        f"{index}_"
        f"{timestamp:.2f}s.jpg"
    )


    evidence_path = os.path.join(
        EVIDENCE_DIR,
        filename
    )


    cv2.imwrite(
        evidence_path,
        frame
    )


    # --------------------------------------------------------
    # CREATE SMART BUS EVENT
    # --------------------------------------------------------

    event = create_event(

        event_type="pothole",

        confidence=best["confidence"],

        bus_id=location["bus_id"],

        video_timestamp=timestamp,

        latitude=location["latitude"],

        longitude=location["longitude"],

        severity="HIGH",

        evidence_image=evidence_path

    )


    events.append(event)


    # --------------------------------------------------------
    # PRINT EVENT
    # --------------------------------------------------------

    print()
    print("🚧 POTHOLE EVENT")
    print("--------------------------------------------")

    print(
        f"Event: {index}"
    )

    print(
        f"Frame: {frame_number}"
    )

    print(
        f"Time: {timestamp:.2f}s"
    )

    print(
        f"Confidence: "
        f"{best['confidence']:.2%}"
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
# SAVE EVENTS JSON
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


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("============================================")
print(" POTHOLE PROCESSING COMPLETE")
print("============================================")

print(
    f"Total temporal groups: "
    f"{len(groups)}"
)

print(
    f"Total pothole events: "
    f"{len(events)}"
)

print(
    f"Evidence folder:"
)

print(
    EVIDENCE_DIR
)

print(
    f"\nEvents JSON:"
)

print(
    OUTPUT_JSON
)

print("============================================")