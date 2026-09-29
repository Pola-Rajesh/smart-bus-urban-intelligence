from ultralytics import YOLO
import cv2
from collections import Counter

# -----------------------------
# CONFIGURATION
# -----------------------------

MODEL_PATH = "yolo11n.pt"

VIDEO_PATH = r"C:\Projects\smart-bus-urban-intelligence\datasets\road_damage\archive\videos_without_audio\10th July-20231125T045234Z-001\10th July\66_10-07-2023.mp4"

OUTPUT_PATH = "traffic_analysis.mp4"

# COCO vehicle classes used by YOLO
VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}

# -----------------------------
# LOAD MODEL
# -----------------------------

model = YOLO(MODEL_PATH)

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    raise RuntimeError("Could not open video")

fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(
    OUTPUT_PATH,
    fourcc,
    fps,
    (width, height)
)

# Track unique vehicle IDs
seen_vehicle_ids = set()

frame_number = 0

print("Starting traffic analysis...")

while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame_number += 1

    # YOLO + ByteTrack
    results = model.track(
        frame,
        persist=True,
        tracker="bytetrack.yaml",
        conf=0.35,
        verbose=False
    )

    counts = Counter()

    if results[0].boxes is not None:

        boxes = results[0].boxes

        for i in range(len(boxes)):

            cls = int(boxes.cls[i])

            if cls not in VEHICLE_CLASSES:
                continue

            vehicle_type = VEHICLE_CLASSES[cls]

            counts[vehicle_type] += 1

            # Tracking ID
            if boxes.id is not None:
                track_id = int(boxes.id[i])
                seen_vehicle_ids.add(track_id)

    # Current vehicles
    current_vehicles = sum(counts.values())

    # -----------------------------
    # TRAFFIC DENSITY
    # -----------------------------

    if current_vehicles <= 5:
        density = "LOW"

    elif current_vehicles <= 12:
        density = "MEDIUM"

    else:
        density = "HIGH"

    # -----------------------------
    # DISPLAY INFORMATION
    # -----------------------------

    cv2.rectangle(
        frame,
        (10, 10),
        (360, 150),
        (0, 0, 0),
        -1
    )

    cv2.putText(
        frame,
        f"Traffic: {density}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Current Vehicles: {current_vehicles}",
        (20, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Cars: {counts['car']}",
        (20, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Bikes: {counts['motorcycle']}",
        (140, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Buses: {counts['bus']}",
        (20, 130),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Trucks: {counts['truck']}",
        (140, 130),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    out.write(frame)

    # Progress every 100 frames
    if frame_number % 100 == 0:
        print(
            f"Frame {frame_number} | "
            f"Vehicles: {current_vehicles} | "
            f"Density: {density}"
        )

cap.release()
out.release()

print("\nTraffic analysis completed!")
print(f"Unique vehicles observed: {len(seen_vehicle_ids)}")
print(f"Output saved to: {OUTPUT_PATH}")