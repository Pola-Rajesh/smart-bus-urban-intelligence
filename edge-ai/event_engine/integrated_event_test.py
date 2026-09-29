import sys
import os

# Allow Python to find the GPS module
GPS_PATH = r"C:\Projects\smart-bus-urban-intelligence\gps\tracks"

sys.path.insert(0, GPS_PATH)

from gps_lookup import load_gps_track, get_location
from event_engine import create_event


# ---------------------------------
# LOAD GPS TRACK
# ---------------------------------

gps_file = os.path.join(
    GPS_PATH,
    "bus_07_track.csv"
)

track = load_gps_track(gps_file)


# ---------------------------------
# SIMULATED AI DETECTION
# ---------------------------------

event_type = "waterlogging"
confidence = 0.82

video_timestamp = 27.0


# ---------------------------------
# GET GPS AUTOMATICALLY
# ---------------------------------

location = get_location(
    video_timestamp,
    track
)


# ---------------------------------
# CREATE EVENT
# ---------------------------------

event = create_event(
    event_type=event_type,
    confidence=confidence,

    bus_id=location["bus_id"],

    video_timestamp=video_timestamp,

    latitude=location["latitude"],
    longitude=location["longitude"],

    severity="HIGH",

    evidence_image="waterlogging_27s.jpg"
)


# ---------------------------------
# DISPLAY
# ---------------------------------

print("\n================================")
print("     SMART BUS AI EVENT")
print("================================")

for key, value in event.items():
    print(f"{key}: {value}")

print("================================")