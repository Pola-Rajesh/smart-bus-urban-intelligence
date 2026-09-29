import sys
import os
import json
import cv2

from collections import Counter

from ultralytics import YOLO


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = r"C:\Projects\smart-bus-urban-intelligence"

MODEL_PATH = (
    PROJECT_ROOT
    + r"\edge-ai\vehicle_detection\yolo11n.pt"
)

VIDEO_PATH = (
    PROJECT_ROOT
    + r"\datasets\road_damage\archive\videos_without_audio"
    + r"\10th July-20231125T045234Z-001\10th July"
    + r"\66_10-07-2023.mp4"
)

GPS_PATH = PROJECT_ROOT + r"\gps\tracks"

GPS_FILE = GPS_PATH + r"\bus_07_track.csv"

EVIDENCE_DIR = (
    PROJECT_ROOT
    + r"\evidence\traffic"
)

OUTPUT_JSON = (
    PROJECT_ROOT
    + r"\evidence\traffic_events.json"
)


# ============================================================
# GPS MODULE
# ============================================================

sys.path.insert(
    0,
    GPS_PATH
)

from gps_lookup import (
    load_gps_track,
    get_location
)


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

CONFIDENCE_THRESHOLD = 0.35

MAX_VIDEO_SECONDS = 60

# Number of consecutive frames required
# before considering traffic a persistent condition.
MIN_GROUP_FRAMES = 5


# ============================================================
# VEHICLE CLASSES
# ============================================================

VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}


# ============================================================
# TRAFFIC LEVEL
# ============================================================

def get_traffic_level(vehicle_count):

    if vehicle_count <= 5:
        return "LOW"

    elif vehicle_count <= 12:
        return "MEDIUM"

    else:
        return "HIGH"


# ============================================================
# PREPARE FOLDERS
# ============================================================

os.makedirs(
    EVIDENCE_DIR,
    exist_ok=True
)


# ============================================================
# LOAD MODEL + GPS
# ============================================================

print()
print("============================================")
print(" SMART BUS TRAFFIC EVENT DETECTOR")
print("============================================")

print()
print("Loading traffic model...")

model = YOLO(MODEL_PATH)

print("Model loaded successfully.")

print("Loading GPS track...")

gps_track = load_gps_track(
    GPS_FILE
)

print("GPS track loaded successfully.")


# ============================================================
# OPEN VIDEO
# ============================================================

print("Opening video...")

cap = cv2.VideoCapture(
    VIDEO_PATH
)

if not cap.isOpened():

    raise RuntimeError(
        "Could not open video:\n"
        + VIDEO_PATH
    )


fps = cap.get(
    cv2.CAP_PROP_FPS
)

total_frames = int(
    cap.get(
        cv2.CAP_PROP_FRAME_COUNT
    )
)

video_duration = (
    total_frames / fps
    if fps > 0
    else 0
)

processing_duration = min(
    video_duration,
    MAX_VIDEO_SECONDS
)


print()
print("--------------------------------------------")
print(
    f"FPS: {fps:.2f}"
)
print(
    f"Total frames: {total_frames}"
)
print(
    f"Video duration: {video_duration:.2f} sec"
)
print(
    f"Processing: {processing_duration:.2f} sec"
)
print("--------------------------------------------")
print()


# ============================================================
# DETECTION STORAGE
# ============================================================

frame_records = []

frame_number = 0


# ============================================================
# PROCESS VIDEO
# ============================================================

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


    # --------------------------------------------------------
    # YOLO + BYTE TRACK
    # --------------------------------------------------------

    results = model.track(
        frame,
        persist=True,
        tracker="bytetrack.yaml",
        conf=CONFIDENCE_THRESHOLD,
        verbose=False
    )

    result = results[0]

    counts = Counter()

    boxes_to_draw = []


    if result.boxes is not None:

        boxes = result.boxes

        for i in range(
            len(boxes)
        ):

            cls = int(
                boxes.cls[i]
            )

            if cls not in VEHICLE_CLASSES:
                continue

            vehicle_type = (
                VEHICLE_CLASSES[cls]
            )

            counts[
                vehicle_type
            ] += 1


            # Bounding box
            xyxy = (
                boxes.xyxy[i]
                .cpu()
                .numpy()
            )

            boxes_to_draw.append(
                (
                    xyxy,
                    vehicle_type
                )
            )


    # --------------------------------------------------------
    # CURRENT VEHICLE COUNT
    # --------------------------------------------------------

    current_vehicles = sum(
        counts.values()
    )


    traffic_level = get_traffic_level(
        current_vehicles
    )


    # --------------------------------------------------------
    # STORE FRAME INFORMATION
    # --------------------------------------------------------

    frame_records.append({

        "frame": frame_number,

        "timestamp": video_timestamp,

        "vehicle_count":
            current_vehicles,

        "traffic_level":
            traffic_level,

        "counts": {

            "car":
                counts["car"],

            "motorcycle":
                counts["motorcycle"],

            "bus":
                counts["bus"],

            "truck":
                counts["truck"]
        },

        "boxes":
            boxes_to_draw
    })


    # --------------------------------------------------------
    # PROGRESS
    # --------------------------------------------------------

    if frame_number % 100 == 0:

        print(
            f"Frame {frame_number} | "
            f"Vehicles: {current_vehicles} | "
            f"Traffic: {traffic_level}"
        )


# ============================================================
# CLEAN UP VIDEO
# ============================================================

cap.release()


# ============================================================
# DETECTION SUMMARY
# ============================================================

print()
print("============================================")
print(" TRAFFIC DETECTION SUMMARY")
print("============================================")

print(
    f"Frames processed: "
    f"{len(frame_records)}"
)


if frame_records:

    total_vehicle_observations = sum(
        record["vehicle_count"]
        for record in frame_records
    )

    average_vehicles = (
        total_vehicle_observations
        / len(frame_records)
    )

else:

    average_vehicles = 0


print(
    f"Average vehicles/frame: "
    f"{average_vehicles:.2f}"
)

print("============================================")
print()


# ============================================================
# FIND HIGH TRAFFIC GROUPS
# ============================================================

traffic_groups = []

current_group = []

for record in frame_records:

    if record["traffic_level"] in (
        "MEDIUM",
        "HIGH"
    ):

        if not current_group:

            current_group = [
                record
            ]

        else:

            previous_frame = (
                current_group[-1]["frame"]
            )

            if (
                record["frame"]
                == previous_frame + 1
            ):

                current_group.append(
                    record
                )

            else:

                if len(
                    current_group
                ) >= MIN_GROUP_FRAMES:

                    traffic_groups.append(
                        current_group
                    )

                current_group = [
                    record
                ]

    else:

        if len(
            current_group
        ) >= MIN_GROUP_FRAMES:

            traffic_groups.append(
                current_group
            )

        current_group = []


# Add final group

if len(
    current_group
) >= MIN_GROUP_FRAMES:

    traffic_groups.append(
        current_group
    )


# ============================================================
# GROUP SUMMARY
# ============================================================

print("============================================")
print(" TEMPORAL TRAFFIC GROUPS")
print("============================================")


for index, group in enumerate(
    traffic_groups,
    start=1
):

    best_record = max(
        group,
        key=lambda x:
        x["vehicle_count"]
    )

    print(
        f"Group #{index}: "
        f"frames "
        f"{group[0]['frame']}-"
        f"{group[-1]['frame']} | "
        f"{group[0]['timestamp']:.2f}-"
        f"{group[-1]['timestamp']:.2f}s | "
        f"frames={len(group)} | "
        f"peak_vehicles="
        f"{best_record['vehicle_count']} | "
        f"level="
        f"{best_record['traffic_level']}"
    )


print("============================================")
print()


# ============================================================
# CREATE TRAFFIC EVENTS
# ============================================================

events = []


for event_number, group in enumerate(
    traffic_groups,
    start=1
):

    # --------------------------------------------------------
    # Select frame with maximum vehicle count
    # --------------------------------------------------------

    best_record = max(
        group,
        key=lambda x:
        x["vehicle_count"]
    )

    timestamp = (
        best_record["timestamp"]
    )

    location = get_location(
        timestamp,
        gps_track
    )


    # --------------------------------------------------------
    # RE-READ BEST FRAME
    # --------------------------------------------------------

    cap = cv2.VideoCapture(
        VIDEO_PATH
    )

    cap.set(
        cv2.CAP_PROP_POS_FRAMES,
        best_record["frame"] - 1
    )

    ret, frame = cap.read()

    cap.release()


    if not ret:

        print(
            f"Could not read evidence "
            f"frame {best_record['frame']}"
        )

        continue


    # --------------------------------------------------------
    # DRAW VEHICLE BOXES
    # --------------------------------------------------------

    for box, vehicle_type in (
        best_record["boxes"]
    ):

        x1, y1, x2, y2 = map(
            int,
            box
        )

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (255, 0, 0),
            2
        )

        cv2.putText(
            frame,
            vehicle_type,
            (x1, max(y1 - 8, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 0, 0),
            2
        )


    # --------------------------------------------------------
    # EVENT INFORMATION
    # --------------------------------------------------------

    label = (
        f"Traffic: "
        f"{best_record['traffic_level']} | "
        f"Vehicles: "
        f"{best_record['vehicle_count']}"
    )

    cv2.putText(
        frame,
        label,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 255),
        2
    )


    # --------------------------------------------------------
    # SAVE EVIDENCE
    # --------------------------------------------------------

    evidence_filename = (
        f"traffic_{event_number}_"
        f"{timestamp:.2f}s.jpg"
    )

    evidence_path = os.path.join(
        EVIDENCE_DIR,
        evidence_filename
    )

    cv2.imwrite(
        evidence_path,
        frame
    )


    # --------------------------------------------------------
    # CREATE EVENT
    # --------------------------------------------------------

    event = create_event(

        event_type="traffic",

        confidence=1.0,

        bus_id=location["bus_id"],

        video_timestamp=timestamp,

        latitude=location["latitude"],

        longitude=location["longitude"],

        severity=(
            "HIGH"
            if best_record[
                "traffic_level"
            ] == "HIGH"
            else "MEDIUM"
        ),

        evidence_image=evidence_path,

        extra_data={

            "traffic_level":
                best_record[
                    "traffic_level"
                ],

            "vehicle_count":
                best_record[
                    "vehicle_count"
                ],

            "cars":
                best_record[
                    "counts"
                ]["car"],

            "motorcycles":
                best_record[
                    "counts"
                ]["motorcycle"],

            "buses":
                best_record[
                    "counts"
                ]["bus"],

            "trucks":
                best_record[
                    "counts"
                ]["truck"],

            "group_frames":
                len(group),

            "start_timestamp":
                group[0][
                    "timestamp"
                ],

            "end_timestamp":
                group[-1][
                    "timestamp"
                ]
        }
    )


    events.append(
        event
    )


    # --------------------------------------------------------
    # DISPLAY EVENT
    # --------------------------------------------------------

    print()
    print("🚦 TRAFFIC EVENT")
    print("--------------------------------------------")

    print(
        f"Event: {event_number}"
    )

    print(
        f"Time: {timestamp:.2f}s"
    )

    print(
        f"Traffic level: "
        f"{best_record['traffic_level']}"
    )

    print(
        f"Vehicles: "
        f"{best_record['vehicle_count']}"
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


# ============================================================
# COMPLETE
# ============================================================

print()
print("============================================")
print(" TRAFFIC PROCESSING COMPLETE")
print("============================================")

print(
    f"Total temporal groups: "
    f"{len(traffic_groups)}"
)

print(
    f"Total traffic events: "
    f"{len(events)}"
)

print()
print("Evidence folder:")
print(EVIDENCE_DIR)

print()
print("Events JSON:")
print(OUTPUT_JSON)

print("============================================")