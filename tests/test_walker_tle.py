"""Walker TLEs must parse to the intended RAAN and mean anomaly. SGP4
reads fixed columns, so a formatting slip silently zeroes a field."""

import math

from sgp4.api import Satrec

from leo_edge.orbit.constellation import generate_walker_delta_tles


def test_walker_tles_parse_to_intended_raan_and_mean_anomaly():
    tles = generate_walker_delta_tles(8, 4, 1, 550.0, 97.4)
    parsed = {}
    for t in tles:
        s = Satrec.twoline2rv(t["line1"], t["line2"])
        parsed[t["sat_id"]] = (math.degrees(s.nodeo), math.degrees(s.mo))
    assert parsed["P0S0"] == (0.0, 0.0) or all(abs(a - b) < 1e-3 for a, b in zip(parsed["P0S0"], (0.0, 0.0)))
    assert abs(parsed["P0S1"][1] - 180.0) < 1e-3
    assert abs(parsed["P1S0"][0] - 90.0) < 1e-3
    assert abs(parsed["P1S0"][1] - 45.0) < 1e-3  # F*360/T = 45 deg
    assert len({round(v[1], 3) for v in parsed.values()}) > 1


def test_satellites_in_one_plane_have_distinct_ground_tracks():
    from leo_edge.orbit.constellation import per_satellite_access_windows
    tles = generate_walker_delta_tles(2, 1, 0, 550.0, 97.4)
    w = per_satellite_access_windows(tles, 40.0, 0.0, 10.0, 24.0)
    starts = {k: [x["start"] for x in v] for k, v in w.items()}
    assert starts["P0S0"] != starts["P0S1"]
