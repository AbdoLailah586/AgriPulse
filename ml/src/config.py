"""Shared paths and constants for the ML pipeline (WS1)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = ROOT / "data" / "raw" / "sensor.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "ml" / "reports"

SENSOR_PREFIX = "sensor_"
STATUS_COL = "machine_status"
TS_COL = "timestamp"

# T09 — sensor handling decisions (see ml/reports/sensor_handling.md)
DROP_SENSORS = ["sensor_15"]  # 100% missing
FFILL_THEN_MEDIAN_SENSORS = ["sensor_50"]  # 34.96% missing, large gaps
INTERPOLATE_SENSORS = ["sensor_51"]  # 6.98% missing, scattered short gaps
MAX_INTERP_GAP = 30  # minutes; longer gaps are flagged, not silently filled.
# Calibrated from the actual gap distribution (ml/reports/sensor_handling.md): most
# sensors share a brief ~8min synchronized dropout (safe to interpolate); a handful
# have gaps in the thousands/tens-of-thousands of minutes (must NOT be interpolated).
# There's no gap length between ~41min and ~4200min in the data, so 30min cleanly
# separates "sensor blip" from "sustained outage" without a judgment call in between.

# T10 — prognostic labeling
WARNING_WINDOWS_MIN = [360, 480, 720]  # 6h, 8h, 12h — swept per the plan
DEFAULT_WARNING_WINDOW_MIN = 720
RUL_CAP_MIN = DEFAULT_WARNING_WINDOW_MIN  # RUL target is only meaningful inside the warning horizon

# T11 — validation
PURGE_MIN = 360  # gap between train/val >= longest rolling feature window (6h)

# T12 — feature engineering
ROLLING_WINDOWS_MIN = [15, 60, 360]  # 15min, 1h, 6h
EWM_SPAN_MIN = 15
# Sensors hypothesized as vibration/current-like (physics mapping in docs/ — treat as
# a hypothesis to validate, not a confirmed fact, since sensor semantics are anonymized).
FFT_CANDIDATE_SENSORS = [
    "sensor_00", "sensor_01",  # vibration (hypothesis)
    "sensor_10", "sensor_11", "sensor_12",  # motor current/load (hypothesis)
]
FFT_WINDOW_MIN = 60
