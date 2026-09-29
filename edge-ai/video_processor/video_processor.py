import cv2
import sys
from pathlib import Path
from ultralytics import YOLO


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ============================================================
# GPS TRACK CONFIGURATION
# ============================================================

GPS_TRACK_FILE = (
    PROJECT_ROOT
    / "gps"
    / "tracks"
    / "bus_07_track.csv"
)

GPS_TRACK_DIR = (
    PROJECT_ROOT
    / "gps"
    / "tracks"
)


if str(GPS_TRACK_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(GPS_TRACK_DIR)
    )


from gps_lookup import (
    load_gps_track,
    get_location
)


# ============================================================
# LOAD GPS TRACK
# ============================================================

if not GPS_TRACK_FILE.exists():

    raise FileNotFoundError(
        "GPS track file not found:\n"
        f"{GPS_TRACK_FILE}"
    )


gps_track = load_gps_track(
    str(GPS_TRACK_FILE)
)


if not gps_track:

    raise RuntimeError(
        "GPS track is empty."
    )


print(
    f"GPS track loaded successfully: "
    f"{len(gps_track)} points"
)


# ============================================================
# MODEL PATHS
# ============================================================

POTHOLE_MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "road_damage"
    / "pothole_v2_yolo11n"
    / "weights"
    / "best.pt"
)


WATERLOGGING_MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "waterlogging"
    / "waterlogging_yolo11n"
    / "weights"
    / "best.pt"
)


# ============================================================
# TRAFFIC MODEL
# ============================================================

TRAFFIC_MODEL_PATH = (
    PROJECT_ROOT
    / "edge-ai"
    / "vehicle_detection"
    / "yolo11n.pt"
)


# ============================================================
# EVIDENCE DIRECTORIES
# ============================================================

POTHOLE_EVIDENCE_DIR = (
    PROJECT_ROOT
    / "evidence"
    / "pothole"
)


WATERLOGGING_EVIDENCE_DIR = (
    PROJECT_ROOT
    / "evidence"
    / "waterlogging"
)


TRAFFIC_EVIDENCE_DIR = (
    PROJECT_ROOT
    / "evidence"
    / "traffic"
)


POTHOLE_EVIDENCE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


WATERLOGGING_EVIDENCE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


TRAFFIC_EVIDENCE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# EVENT ENGINE
# ============================================================

EVENT_ENGINE_DIR = (
    PROJECT_ROOT
    / "edge-ai"
    / "event_engine"
)


if str(EVENT_ENGINE_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(EVENT_ENGINE_DIR)
    )


from event_engine import create_event


# ============================================================
# LOAD MODELS
# ============================================================

print()
print("============================================")
print(" SMART BUS AI MODEL INITIALIZATION")
print("============================================")


# ============================================================
# POTHOLE MODEL
# ============================================================

print("Loading pothole model...")


if not POTHOLE_MODEL_PATH.exists():

    raise FileNotFoundError(
        "Pothole model not found:\n"
        f"{POTHOLE_MODEL_PATH}"
    )


pothole_model = YOLO(
    str(POTHOLE_MODEL_PATH)
)


print(
    "Pothole model loaded successfully."
)


# ============================================================
# WATERLOGGING MODEL
# ============================================================

print("Loading waterlogging model...")


if not WATERLOGGING_MODEL_PATH.exists():

    raise FileNotFoundError(
        "Waterlogging model not found:\n"
        f"{WATERLOGGING_MODEL_PATH}"
    )


waterlogging_model = YOLO(
    str(WATERLOGGING_MODEL_PATH)
)


print(
    "Waterlogging model loaded successfully."
)


# ============================================================
# TRAFFIC MODEL
# ============================================================

print("Loading traffic model...")


if TRAFFIC_MODEL_PATH.exists():

    traffic_model = YOLO(
        str(TRAFFIC_MODEL_PATH)
    )

    print(
        "Traffic model loaded successfully."
    )

else:

    traffic_model = None

    print(
        "WARNING: Traffic model not found."
    )

    print(
        f"Expected:\n{TRAFFIC_MODEL_PATH}"
    )


print("============================================")
print(" ALL AI MODELS INITIALIZED")
print("============================================")
print()


# ============================================================
# CONFIGURATION
# ============================================================

POTHOLE_CONFIDENCE = 0.40

WATERLOGGING_CONFIDENCE = 0.40

TRAFFIC_CONFIDENCE = 0.40


# Prevent excessive duplicate events.

POTHOLE_EVENT_INTERVAL = 1.0

WATERLOGGING_EVENT_INTERVAL = 2.0

TRAFFIC_EVENT_INTERVAL = 3.0


# ============================================================
# BUS CONFIGURATION
# ============================================================

# The current prototype uses the GPS track belonging to BUS-07.
#
# Later this can become dynamic when multiple buses are added.

DEFAULT_BUS_ID = "BUS-07"


# ============================================================
# EVENT VALUE HELPER
# ============================================================

def get_event_value(
    event,
    key,
    default=None
):
    """
    Supports both:
        event.attribute
    and:
        event["attribute"]

    This keeps the processor compatible with
    the existing event engine implementation.
    """

    if event is None:

        return default


    # Dictionary-style event

    if isinstance(event, dict):

        return event.get(
            key,
            default
        )


    # Object-style event

    return getattr(
        event,
        key,
        default
    )


# ============================================================
# DETECTION HELPER
# ============================================================

def get_best_detection(
    result,
    confidence_threshold
):

    if result.boxes is None:

        return None, 0.0


    best_box = None

    best_confidence = 0.0


    for box in result.boxes:

        confidence = float(
            box.conf[0]
        )


        if confidence < confidence_threshold:

            continue


        if confidence > best_confidence:

            best_confidence = confidence

            best_box = (
                box.xyxy[0]
                .cpu()
                .numpy()
            )


    return (
        best_box,
        best_confidence
    )


# ============================================================
# DRAW DETECTION
# ============================================================

def draw_detection(
    frame,
    box,
    label,
    confidence
):

    annotated = frame.copy()


    if box is not None:

        x1, y1, x2, y2 = map(
            int,
            box
        )


        cv2.rectangle(
            annotated,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )


        text = (
            f"{label} "
            f"{confidence * 100:.1f}%"
        )


        cv2.putText(
            annotated,
            text,
            (
                x1,
                max(
                    y1 - 10,
                    20
                )
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )


    return annotated


# ============================================================
# GET GPS LOCATION FOR VIDEO TIMESTAMP
# ============================================================

def get_video_location(
    timestamp
):

    location = get_location(
        timestamp,
        gps_track
    )


    latitude = location[
        "latitude"
    ]


    longitude = location[
        "longitude"
    ]


    bus_id = location.get(
        "bus_id",
        DEFAULT_BUS_ID
    )


    return (
        bus_id,
        latitude,
        longitude
    )


# ============================================================
# PROCESS VIDEO
# ============================================================

def process_video(video_path):

    video_path = Path(
        video_path
    )


    if not video_path.exists():

        raise FileNotFoundError(
            f"Video not found: {video_path}"
        )


    print()
    print("============================================")
    print(" SMART BUS MULTI-MODEL VIDEO PROCESSOR")
    print("============================================")

    print(
        f"Video: {video_path}"
    )

    print(
        f"GPS Track: {GPS_TRACK_FILE}"
    )

    print("============================================")


    # ========================================================
    # OPEN VIDEO
    # ========================================================

    cap = cv2.VideoCapture(
        str(video_path)
    )


    if not cap.isOpened():

        raise RuntimeError(
            "Unable to open video."
        )


    fps = cap.get(
        cv2.CAP_PROP_FPS
    )


    total_frames = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )


    if fps <= 0:

        raise RuntimeError(
            "Unable to determine video FPS."
        )


    duration = (
        total_frames / fps
    )


    print(
        f"FPS: {fps:.2f}"
    )


    print(
        f"Total frames: {total_frames}"
    )


    print(
        f"Duration: {duration:.2f} seconds"
    )


    print(
        "============================================"
    )


    # ========================================================
    # STATE
    # ========================================================

    frame_number = 0


    events = []


    last_pothole_timestamp = -999

    last_waterlogging_timestamp = -999

    last_traffic_timestamp = -999


    # ========================================================
    # PROCESS FRAMES
    # ========================================================

    while True:

        success, frame = cap.read()


        if not success:

            break


        frame_number += 1


        # ----------------------------------------------------
        # VIDEO TIMESTAMP
        # ----------------------------------------------------
        #
        # First frame = 0.0 seconds
        #

        timestamp = (
            (frame_number - 1)
            / fps
        )


        # ====================================================
        # GPS LOOKUP
        # ====================================================

        (
            bus_id,
            latitude,
            longitude
        ) = get_video_location(
            timestamp
        )


        # ====================================================
        # 1. POTHOLE DETECTION
        # ====================================================

        pothole_results = pothole_model(
            frame,
            verbose=False
        )


        pothole_result = (
            pothole_results[0]
        )


        (
            pothole_box,
            pothole_confidence
        ) = get_best_detection(
            pothole_result,
            POTHOLE_CONFIDENCE
        )


        if pothole_box is not None:

            if (
                timestamp
                - last_pothole_timestamp
                >= POTHOLE_EVENT_INTERVAL
            ):

                annotated = draw_detection(
                    frame,
                    pothole_box,
                    "POTHOLE",
                    pothole_confidence
                )


                # GPS information on evidence

                gps_text = (
                    f"{bus_id} | "
                    f"GPS: "
                    f"{latitude:.6f}, "
                    f"{longitude:.6f}"
                )


                cv2.putText(
                    annotated,
                    gps_text,
                    (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 255, 255),
                    2
                )


                evidence_filename = (
                    f"pothole_"
                    f"{frame_number}_"
                    f"{timestamp:.2f}s.jpg"
                )


                evidence_path = (
                    POTHOLE_EVIDENCE_DIR
                    / evidence_filename
                )


                cv2.imwrite(
                    str(evidence_path),
                    annotated
                )


                severity = (
                    "HIGH"
                    if pothole_confidence >= 0.70
                    else "MEDIUM"
                )


                event = create_event(

                    event_type="pothole",

                    confidence=pothole_confidence,

                    bus_id=bus_id,

                    video_timestamp=timestamp,

                    latitude=latitude,

                    longitude=longitude,

                    severity=severity,

                    evidence_image=str(
                        evidence_path
                    ),

                    extra_data={

                        "detector":
                            "YOLO11n",

                        "model":
                            "pothole_v2_yolo11n",

                        "frame_number":
                            frame_number
                    }
                )


                events.append(
                    event
                )


                last_pothole_timestamp = (
                    timestamp
                )


                print(
                    f"[POTHOLE] "
                    f"{timestamp:.2f}s | "
                    f"{pothole_confidence:.2%} | "
                    f"{bus_id} | "
                    f"{latitude:.6f}, "
                    f"{longitude:.6f}"
                )


        # ====================================================
        # 2. WATERLOGGING DETECTION
        # ====================================================

        water_results = (
            waterlogging_model(
                frame,
                verbose=False
            )
        )


        water_result = (
            water_results[0]
        )


        (
            water_box,
            water_confidence
        ) = get_best_detection(
            water_result,
            WATERLOGGING_CONFIDENCE
        )


        if water_box is not None:

            if (
                timestamp
                - last_waterlogging_timestamp
                >= WATERLOGGING_EVENT_INTERVAL
            ):

                annotated = draw_detection(
                    frame,
                    water_box,
                    "WATERLOGGING",
                    water_confidence
                )


                gps_text = (
                    f"{bus_id} | "
                    f"GPS: "
                    f"{latitude:.6f}, "
                    f"{longitude:.6f}"
                )


                cv2.putText(
                    annotated,
                    gps_text,
                    (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 255, 255),
                    2
                )


                evidence_filename = (
                    f"waterlogging_"
                    f"{frame_number}_"
                    f"{timestamp:.2f}s.jpg"
                )


                evidence_path = (
                    WATERLOGGING_EVIDENCE_DIR
                    / evidence_filename
                )


                cv2.imwrite(
                    str(evidence_path),
                    annotated
                )


                severity = (
                    "HIGH"
                    if water_confidence >= 0.70
                    else "MEDIUM"
                )


                event = create_event(

                    event_type="waterlogging",

                    confidence=water_confidence,

                    bus_id=bus_id,

                    video_timestamp=timestamp,

                    latitude=latitude,

                    longitude=longitude,

                    severity=severity,

                    evidence_image=str(
                        evidence_path
                    ),

                    extra_data={

                        "detector":
                            "YOLO11n",

                        "model":
                            "waterlogging_yolo11n",

                        "frame_number":
                            frame_number
                    }
                )


                events.append(
                    event
                )


                last_waterlogging_timestamp = (
                    timestamp
                )


                print(
                    f"[WATERLOGGING] "
                    f"{timestamp:.2f}s | "
                    f"{water_confidence:.2%} | "
                    f"{bus_id} | "
                    f"{latitude:.6f}, "
                    f"{longitude:.6f}"
                )


        # ====================================================
        # 3. TRAFFIC DETECTION
        # ====================================================

        if traffic_model is not None:

            traffic_results = (
                traffic_model(
                    frame,
                    verbose=False
                )
            )


            traffic_result = (
                traffic_results[0]
            )


            vehicle_count = 0


            best_vehicle_box = None

            best_vehicle_confidence = 0.0


            if traffic_result.boxes is not None:

                for box in traffic_result.boxes:

                    confidence = float(
                        box.conf[0]
                    )


                    if confidence < TRAFFIC_CONFIDENCE:

                        continue


                    class_id = int(
                        box.cls[0]
                    )


                    # COCO vehicle classes:
                    #
                    # 2 = car
                    # 3 = motorcycle
                    # 5 = bus
                    # 7 = truck

                    vehicle_classes = {
                        2,
                        3,
                        5,
                        7
                    }


                    if class_id not in vehicle_classes:

                        continue


                    vehicle_count += 1


                    if (
                        confidence
                        > best_vehicle_confidence
                    ):

                        best_vehicle_confidence = (
                            confidence
                        )


                        best_vehicle_box = (
                            box.xyxy[0]
                            .cpu()
                            .numpy()
                        )


            # ------------------------------------------------
            # TRAFFIC CONDITION
            # ------------------------------------------------

            traffic_detected = (
                vehicle_count >= 5
            )


            if traffic_detected:

                if (
                    timestamp
                    - last_traffic_timestamp
                    >= TRAFFIC_EVENT_INTERVAL
                ):

                    annotated = (
                        frame.copy()
                    )


                    # Draw strongest vehicle

                    if (
                        best_vehicle_box
                        is not None
                    ):

                        x1, y1, x2, y2 = map(
                            int,
                            best_vehicle_box
                        )


                        cv2.rectangle(
                            annotated,
                            (x1, y1),
                            (x2, y2),
                            (255, 165, 0),
                            2
                        )


                    traffic_label = (
                        f"TRAFFIC | "
                        f"Vehicles: "
                        f"{vehicle_count}"
                    )


                    cv2.putText(
                        annotated,
                        traffic_label,
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (255, 165, 0),
                        2
                    )


                    gps_text = (
                        f"{bus_id} | "
                        f"GPS: "
                        f"{latitude:.6f}, "
                        f"{longitude:.6f}"
                    )


                    cv2.putText(
                        annotated,
                        gps_text,
                        (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 255, 255),
                        2
                    )


                    evidence_filename = (
                        f"traffic_"
                        f"{frame_number}_"
                        f"{timestamp:.2f}s.jpg"
                    )


                    evidence_path = (
                        TRAFFIC_EVIDENCE_DIR
                        / evidence_filename
                    )


                    cv2.imwrite(
                        str(evidence_path),
                        annotated
                    )


                    traffic_confidence = (
                        best_vehicle_confidence
                        if best_vehicle_confidence > 0
                        else 0.50
                    )


                    event = create_event(

                        event_type="traffic",

                        confidence=traffic_confidence,

                        bus_id=bus_id,

                        video_timestamp=timestamp,

                        latitude=latitude,

                        longitude=longitude,

                        severity="MEDIUM",

                        evidence_image=str(
                            evidence_path
                        ),

                        extra_data={

                            "detector":
                                "YOLO11n-Coco",

                            "model":
                                "yolo11n.pt",

                            "vehicle_count":
                                vehicle_count,

                            "frame_number":
                                frame_number
                        }
                    )


                    events.append(
                        event
                    )


                    last_traffic_timestamp = (
                        timestamp
                    )


                    print(
                        f"[TRAFFIC] "
                        f"{timestamp:.2f}s | "
                        f"vehicles="
                        f"{vehicle_count} | "
                        f"{bus_id} | "
                        f"{latitude:.6f}, "
                        f"{longitude:.6f}"
                    )


    # ========================================================
    # CLEANUP
    # ========================================================

    cap.release()


    # ========================================================
    # SORT EVENTS
    # ========================================================

    events.sort(
        key=lambda event:
            float(
                get_event_value(
                    event,
                    "video_timestamp",
                    0
                )
            )
    )


    # ========================================================
    # SUMMARY
    # ========================================================

    pothole_count = sum(

        1

        for event in events

        if get_event_value(
            event,
            "event_type"
        )
        == "pothole"
    )


    waterlogging_count = sum(

        1

        for event in events

        if get_event_value(
            event,
            "event_type"
        )
        == "waterlogging"
    )


    traffic_count = sum(

        1

        for event in events

        if get_event_value(
            event,
            "event_type"
        )
        == "traffic"
    )


    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    print()
    print("============================================")
    print(" MULTI-MODEL VIDEO PROCESSING COMPLETE")
    print("============================================")


    print(
        f"Frames processed: "
        f"{frame_number}"
    )


    print(
        f"Pothole events: "
        f"{pothole_count}"
    )


    print(
        f"Waterlogging events: "
        f"{waterlogging_count}"
    )


    print(
        f"Traffic events: "
        f"{traffic_count}"
    )


    print(
        f"TOTAL EVENTS: "
        f"{len(events)}"
    )


    print("============================================")


    # ========================================================
    # GPS VERIFICATION
    # ========================================================

    print()
    print("===== GPS EVENT VERIFICATION =====")


    for event in events:

        event_type = get_event_value(
            event,
            "event_type",
            "unknown"
        )


        event_time = get_event_value(
            event,
            "video_timestamp",
            0
        )


        event_bus = get_event_value(
            event,
            "bus_id",
            DEFAULT_BUS_ID
        )


        event_lat = get_event_value(
            event,
            "latitude",
            None
        )


        event_lon = get_event_value(
            event,
            "longitude",
            None
        )


        print(
            f"{event_type.upper():15} | "
            f"{event_time:6.2f}s | "
            f"{event_bus} | "
            f"{event_lat:.6f}, "
            f"{event_lon:.6f}"
        )


    print(
        "============================================"
    )


    return events


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    video = (
        PROJECT_ROOT
        / "edge-ai"
        / "vehicle_detection"
        / "traffic_analysis.mp4"
    )


    events = process_video(
        video
    )


    print()
    print(
        "===== GENERATED SMART BUS EVENTS ====="
    )


    for event in events:

        print(
            event
        )