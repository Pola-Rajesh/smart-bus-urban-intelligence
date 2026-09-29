from gps_provider import ReplayGPSProvider


GPS_FILE = (
    r"C:\Projects\smart-bus-urban-intelligence"
    r"\gps\tracks\bus_07_track.csv"
)


gps = ReplayGPSProvider(GPS_FILE)


test_times = [
    0,
    1.07,
    5,
    7.77,
    8.10,
    10,
    60
]


print()
print("============================================")
print(" GPS PROVIDER TEST")
print("============================================")


for timestamp in test_times:

    location = gps.get_location(timestamp)

    print(
        f"Time: {timestamp:>5.2f}s | "
        f"Bus: {location['bus_id']} | "
        f"GPS: "
        f"{location['latitude']:.6f}, "
        f"{location['longitude']:.6f}"
    )


print("============================================")