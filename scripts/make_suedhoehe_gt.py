#!/usr/bin/env python3
"""Build the Suedhoehe GNSS reference trajectory from /fmu/out/vehicle_gps_position.

Output (in the bag folder):
  gt_gnss_tum.txt   t x y z qx qy qz qw  -- local ENU [m] relative to the first valid fix,
                                          identity orientation (GNSS gives position only)
  gt_gnss_meta.csv  t, fix_type, eph, epv, satellites, lat, lon, alt
Only real GNSS samples are written (no resampling onto camera stamps), and only fixes with
fix_type >= 3 (3D or better).

Time base: px4_msgs/SensorGps has no ROS header, only PX4 boot time. The bag receive time
is used instead, which is in the same clock as the camera/IMU header stamps; the GNSS
transport delay (tens of ms) is not compensated and is documented as a limitation.

px4_msgs is not installed in the container, so the CDR payload is decoded by hand using the
schema stored in the MCAP file (fields up to `satellites_used` are needed).

Run inside slam-base:
    python3 scripts/make_suedhoehe_gt.py datasets/suedhoehe_gps_schnee_02
"""
import math
import os
import struct
import sys

import rosbag2_py

TOPIC = "/fmu/out/vehicle_gps_position"
A_WGS84 = 6378137.0
E2_WGS84 = 6.69437999014e-3


class Cdr:
    """Minimal little-endian CDR reader (alignment relative to the end of the 4-byte header)."""

    def __init__(self, buf):
        assert buf[1] == 0x01, "expected little-endian CDR"
        self.buf, self.pos = buf, 4

    def read(self, fmt, size):
        self.pos += (-(self.pos - 4)) % size
        (value,) = struct.unpack_from("<" + fmt, self.buf, self.pos)
        self.pos += size
        return value


def decode(buf):
    r = Cdr(buf)
    msg = {}
    r.read("Q", 8)                      # timestamp
    r.read("Q", 8)                      # timestamp_sample
    r.read("I", 4)                      # device_id
    msg["lat"] = r.read("d", 8)
    msg["lon"] = r.read("d", 8)
    r.read("d", 8)                      # altitude_msl_m
    msg["alt"] = r.read("d", 8)         # altitude_ellipsoid_m (consistent with WGS84 ECEF)
    r.read("f", 4)                      # s_variance_m_s
    r.read("f", 4)                      # c_variance_rad
    msg["fix_type"] = r.read("B", 1)
    msg["eph"] = r.read("f", 4)
    msg["epv"] = r.read("f", 4)
    r.read("f", 4)                      # hdop
    r.read("f", 4)                      # vdop
    r.read("i", 4)                      # noise_per_ms
    r.read("H", 2)                      # automatic_gain_control
    r.read("B", 1)                      # jamming_state
    r.read("i", 4)                      # jamming_indicator
    r.read("B", 1)                      # spoofing_state
    for _ in range(5):
        r.read("f", 4)                  # vel_m_s, vel_n/e/d, cog_rad
    r.read("?", 1)                      # vel_ned_valid
    r.read("i", 4)                      # timestamp_time_relative
    r.read("Q", 8)                      # time_utc_usec
    msg["sats"] = r.read("B", 1)
    return msg


def ecef(lat, lon, alt):
    lat, lon = math.radians(lat), math.radians(lon)
    n = A_WGS84 / math.sqrt(1 - E2_WGS84 * math.sin(lat) ** 2)
    return ((n + alt) * math.cos(lat) * math.cos(lon),
            (n + alt) * math.cos(lat) * math.sin(lon),
            (n * (1 - E2_WGS84) + alt) * math.sin(lat))


def enu(p, ref, lat0, lon0):
    lat0, lon0 = math.radians(lat0), math.radians(lon0)
    d = [p[i] - ref[i] for i in range(3)]
    e = -math.sin(lon0) * d[0] + math.cos(lon0) * d[1]
    n = (-math.sin(lat0) * math.cos(lon0) * d[0] - math.sin(lat0) * math.sin(lon0) * d[1]
         + math.cos(lat0) * d[2])
    u = (math.cos(lat0) * math.cos(lon0) * d[0] + math.cos(lat0) * math.sin(lon0) * d[1]
         + math.sin(lat0) * d[2])
    return e, n, u


def main(bag):
    reader = rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=bag, storage_id="mcap"),
                rosbag2_py.ConverterOptions("cdr", "cdr"))
    reader.set_filter(rosbag2_py.StorageFilter(topics=[TOPIC]))

    samples = []
    while reader.has_next():
        _, data, t_ns = reader.read_next()
        samples.append((t_ns * 1e-9, decode(bytes(data))))
    valid = [(t, m) for t, m in samples if m["fix_type"] >= 3]
    print(f"GNSS messages: {len(samples)}, with 3D fix or better: {len(valid)}")
    if not valid:
        sys.exit("no valid fixes")

    fixes = {}
    for _, m in samples:
        fixes[m["fix_type"]] = fixes.get(m["fix_type"], 0) + 1
    print("fix_type histogram:", dict(sorted(fixes.items())))
    eph = sorted(m["eph"] for _, m in valid)
    print(f"eph median {eph[len(eph) // 2]:.2f} m, max {eph[-1]:.2f} m; "
          f"epv median {sorted(m['epv'] for _, m in valid)[len(valid) // 2]:.2f} m")

    lat0, lon0, alt0 = valid[0][1]["lat"], valid[0][1]["lon"], valid[0][1]["alt"]
    ref = ecef(lat0, lon0, alt0)
    with open(os.path.join(bag, "gt_gnss_tum.txt"), "w") as f_tum, \
            open(os.path.join(bag, "gt_gnss_meta.csv"), "w") as f_meta:
        f_tum.write("# t x_east y_north z_up qx qy qz qw  (GNSS, position only)\n")
        f_meta.write("t,fix_type,eph,epv,satellites,lat,lon,alt_ellipsoid\n")
        last = None
        for t, m in valid:
            key = (m["lat"], m["lon"], m["alt"])
            if key == last:      # receiver repeated the previous solution
                continue
            last = key
            e, n, u = enu(ecef(*key), ref, lat0, lon0)
            f_tum.write(f"{t:.9f} {e:.4f} {n:.4f} {u:.4f} 0 0 0 1\n")
            f_meta.write(f"{t:.9f},{m['fix_type']},{m['eph']:.3f},{m['epv']:.3f},{m['sats']},"
                         f"{m['lat']:.9f},{m['lon']:.9f},{m['alt']:.3f}\n")
    print(f"wrote {os.path.join(bag, 'gt_gnss_tum.txt')}")


if __name__ == "__main__":
    main(sys.argv[1])
