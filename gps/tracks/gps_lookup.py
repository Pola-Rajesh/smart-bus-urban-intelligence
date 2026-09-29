import csv
from bisect import bisect_right

from pathlib import Path

GPS_FILE = Path(__file__).resolve().parent / "bus_07_track.csv"


def load_gps_track(filename):
    track = []

    with open(filename, newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            track.append({
                "timestamp": float(row["timestamp"]),
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "bus_id": row["bus_id"]
            })

    return track


def get_location(timestamp, track):
    timestamps = [p["timestamp"] for p in track]

    # Before first GPS point
    if timestamp <= timestamps[0]:
        return track[0]

    # After last GPS point
    if timestamp >= timestamps[-1]:
        return track[-1]

    # Find surrounding GPS points
    i = bisect_right(timestamps, timestamp) - 1

    p1 = track[i]
    p2 = track[i + 1]

    # Linear interpolation
    ratio = (
        (timestamp - p1["timestamp"]) /
        (p2["timestamp"] - p1["timestamp"])
    )

    latitude = p1["latitude"] + ratio * (
        p2["latitude"] - p1["latitude"]
    )

    longitude = p1["longitude"] + ratio * (
        p2["longitude"] - p1["longitude"]
    )

    return {
        "timestamp": timestamp,
        "latitude": latitude,
        "longitude": longitude,
        "bus_id": p1["bus_id"]
    }
# -----------------------------
# TEST
# -----------------------------

if __name__ == "__main__":

    track = load_gps_track(GPS_FILE)

    test_times = [0, 7, 12, 27, 42, 58]

    for t in test_times:

        location = get_location(t, track)

        print(
            f"Video time: {t:>5.1f}s | "
            f"Bus: {location['bus_id']} | "
            f"GPS: {location['latitude']:.6f}, "
            f"{location['longitude']:.6f}"
        )

