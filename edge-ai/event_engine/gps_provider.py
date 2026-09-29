import sys

GPS_PATH = r"C:\Projects\smart-bus-urban-intelligence\gps\tracks"

sys.path.insert(0, GPS_PATH)

from gps_lookup import load_gps_track, get_location


class ReplayGPSProvider:
    """
    GPS provider that replays a recorded GPS track.

    This is used during prototype development.
    The interface is designed so a live GPS provider
    can replace it later without changing the
    detection services.
    """

    def __init__(self, gps_file):
        self.gps_file = gps_file
        self.track = load_gps_track(gps_file)

        if not self.track:
            raise RuntimeError(
                f"GPS track is empty: {gps_file}"
            )

    def get_location(self, timestamp):
        return get_location(
            timestamp,
            self.track
        )