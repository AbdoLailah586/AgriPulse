"""T08 — Ingest and profile sensor.csv; validate the numbers claimed in docs/."""

import json
from pathlib import Path

import pandas as pd

RAW_PATH = Path(__file__).resolve().parents[2] / "data" / "raw" / "sensor.csv"
REPORT_PATH = Path(__file__).resolve().parents[2] / "ml" / "reports" / "profile_report.json"


def main():
    df = pd.read_csv(RAW_PATH, index_col=0, parse_dates=["timestamp"])

    sensor_cols = [c for c in df.columns if c.startswith("sensor_")]

    missing_pct = (df[sensor_cols].isna().mean() * 100).sort_values(ascending=False)

    status_counts = df["machine_status"].value_counts()
    status_pct = (status_counts / len(df) * 100).round(3)

    broken = df[df["machine_status"] == "BROKEN"]
    breakdown_events = [
        {"row_index": int(idx), "timestamp": str(df.loc[idx, "timestamp"])}
        for idx in broken.index
    ]

    # gaps / duplicate timestamp check
    ts = df["timestamp"]
    is_sorted = ts.is_monotonic_increasing
    diffs = ts.diff().dropna()
    expected = pd.Timedelta(minutes=1)
    n_gaps = int((diffs != expected).sum())
    n_duplicates = int(ts.duplicated().sum())

    report = {
        "n_rows": int(len(df)),
        "n_cols": int(df.shape[1]),
        "n_sensor_cols": len(sensor_cols),
        "time_range": [str(ts.min()), str(ts.max())],
        "timestamps_sorted": bool(is_sorted),
        "n_duplicate_timestamps": n_duplicates,
        "n_non_1min_gaps": n_gaps,
        "machine_status_counts": status_counts.to_dict(),
        "machine_status_pct": status_pct.to_dict(),
        "n_broken_rows": int(len(broken)),
        "breakdown_events": breakdown_events,
        "top_10_missing_sensors_pct": missing_pct.head(10).round(3).to_dict(),
        "sensor_100pct_missing": missing_pct[missing_pct == 100].index.tolist(),
        "sensors_over_30pct_missing": missing_pct[missing_pct > 30].index.tolist(),
        "sensors_over_90pct_complete": (100 - missing_pct[missing_pct < 10]).index.tolist(),
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
