import math
import time
from pathlib import Path

from gps.tracks.gps_lookup import (
    load_gps_track,
    get_location
)


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ============================================================
# GPS TRACK
# ============================================================

GPS_TRACK_FILE = (
    PROJECT_ROOT
    / "gps"
    / "tracks"
    / "bus_07_track.csv"
)


# ============================================================
# LOAD EXISTING BUS-07 TRACK
# ============================================================

BUS_07_TRACK = load_gps_track(
    str(GPS_TRACK_FILE)
)


# ============================================================
# DEMO BUS CONFIGURATION
# ============================================================
#
# BUS-07 uses the existing GPS track.
#
# The other buses use controlled simulated movement
# around the same demonstration area.
#
# Later these can be replaced by real GPS/MQTT data.
# ============================================================

DEMO_BUSES = [

    {
        "bus_id": "BUS-01",
        "name": "Bus 01",
        "base_latitude": 15.828119,
        "base_longitude": 78.037319,
        "route": "Kurnool City",
        "speed": 32
    },

    {
        "bus_id": "BUS-02",
        "name": "Bus 02",
        "base_latitude": 15.832500,
        "base_longitude": 78.045000,
        "route": "Nandyal Road",
        "speed": 27
    },

    {
        "bus_id": "BUS-03",
        "name": "Bus 03",
        "base_latitude": 15.820500,
        "base_longitude": 78.029500,
        "route": "NH-40",
        "speed": 41
    },

    {
        "bus_id": "BUS-04",
        "name": "Bus 04",
        "base_latitude": 15.840000,
        "base_longitude": 78.031000,
        "route": "Kurnool North",
        "speed": 24
    },

    {
        "bus_id": "BUS-05",
        "name": "Bus 05",
        "base_latitude": 15.815000,
        "base_longitude": 78.048000,
        "route": "Kurnool South",
        "speed": 35
    },

    {
        "bus_id": "BUS-07",
        "name": "Bus 07",
        "base_latitude": 15.828119,
        "base_longitude": 78.037319,
        "route": "AI Sensor Bus",
        "speed": 30
    }
]


# ============================================================
# SIMULATED BUS POSITION
# ============================================================

def get_simulated_position(bus, elapsed_seconds):

    base_lat = bus["base_latitude"]
    base_lon = bus["base_longitude"]

    # Small movement around the base coordinate.
    #
    # This is deliberately small so the buses remain
    # inside the demonstration area.

    phase = (
        elapsed_seconds / 12.0
        + int(bus["bus_id"].split("-")[1])
    )

    latitude_offset = (
        math.sin(phase)
        * 0.004
    )

    longitude_offset = (
        math.cos(phase)
        * 0.004
    )

    return {
        "latitude": base_lat + latitude_offset,
        "longitude": base_lon + longitude_offset
    }


# ============================================================
# GET BUS FLEET
# ============================================================

def get_fleet():

    current_time = time.time()

    buses = []

    for bus in DEMO_BUSES:

        bus_id = bus["bus_id"]


        # ----------------------------------------------------
        # BUS-07
        # ----------------------------------------------------
        #
        # Use the existing GPS track.
        #
        # The track is treated as a repeating demonstration
        # track for the live fleet page.
        # ----------------------------------------------------

        if bus_id == "BUS-07":

            track_duration = (
                BUS_07_TRACK[-1]["timestamp"]
                - BUS_07_TRACK[0]["timestamp"]
            )

            if track_duration > 0:

                demo_timestamp = (
                    current_time
                    % track_duration
                )

            else:

                demo_timestamp = 0

            location = get_location(
                demo_timestamp,
                BUS_07_TRACK
            )

            latitude = location["latitude"]
            longitude = location["longitude"]

        else:

            position = get_simulated_position(
                bus,
                current_time
            )

            latitude = position["latitude"]
            longitude = position["longitude"]


        buses.append({

            "bus_id": bus_id,

            "name": bus["name"],

            "latitude": latitude,

            "longitude": longitude,

            "status": "ACTIVE",

            "route": bus["route"],

            "speed": bus["speed"],

            "last_update": current_time

        })

    return buses