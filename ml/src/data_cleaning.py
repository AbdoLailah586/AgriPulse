"""T09 — Clean sensor.csv and decide per-sensor handling.

Deviates from the plan docs' blanket "ffill/interpolate sensor_50 and sensor_51"
instruction: both sensors have single contiguous gaps measured in THOUSANDS of
minutes (sensor_50: ~77,000 min terminal gap covering breakdown event #7 entirely;
sensor_51: ~15,356 min gap covering the full pre-failure window of event #5, the
largest failure in the dataset). Filling gaps that size would fabricate data
through the exact events the model needs to learn from. Policy here: only gaps
<= MAX_INTERP_GAP are filled; longer gaps are left NaN and flagged with a
`<sensor>_was_missing` indicator so downstream models can learn from missingness
instead of being fed invented trends.
"""

import json

import numpy as np
import pandas as pd

from config import (
    DROP_SENSORS,
    MAX_INTERP_GAP,
    RAW_PATH,
    REPORTS_DIR,
    SENSOR_PREFIX,
    STATUS_COL,
    TS_COL,
)


def _longest_nan_run(isna: np.ndarray) -> int:
    if not isna.any():
        return 0
    max_run = run = 0
    for v in isna:
        run = run + 1 if v else 0
        max_run = max(max_run, run)
    return max_run


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(RAW_PATH, index_col=0, parse_dates=[TS_COL])
    return df


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    sensor_cols = [c for c in df.columns if c.startswith(SENSOR_PREFIX)]
    decisions = {}

    df = df.drop(columns=[c for c in DROP_SENSORS if c in df.columns])
    decisions["dropped"] = {c: "100% missing" for c in DROP_SENSORS}

    remaining = [c for c in sensor_cols if c not in DROP_SENSORS]
    std = df[remaining].std()
    near_constant = std[std < 1e-6].index.tolist()
    decisions["near_constant_flagged"] = near_constant  # none found as of T08/T09 EDA, kept for future re-runs

    missing_indicator_cols = []
    gap_actions = {}
    new_indicators = {}
    for col in remaining:
        isna = df[col].isna().to_numpy()
        n_missing = int(isna.sum())
        if n_missing == 0:
            continue
        longest_run = _longest_nan_run(isna)

        if longest_run > MAX_INTERP_GAP:
            # Long gap: do NOT invent data. Flag it with a missingness indicator
            # and leave the value NaN (imputed later, per-fold, if a model requires
            # no-NaN input — e.g. a neutral fill fit on the training fold only).
            ind_col = f"{col}_was_missing"
            new_indicators[ind_col] = isna.astype("int8")
            missing_indicator_cols.append(ind_col)
            gap_actions[col] = {
                "action": "flagged_not_imputed",
                "n_missing": n_missing,
                "longest_gap_min": longest_run,
                "reason": f"longest gap {longest_run}min > {MAX_INTERP_GAP}min threshold",
            }
        else:
            # Short, scattered gaps: safe to linearly interpolate.
            df[col] = df[col].interpolate(method="linear", limit=MAX_INTERP_GAP)
            gap_actions[col] = {
                "action": "linear_interpolated",
                "n_missing": n_missing,
                "longest_gap_min": longest_run,
            }

    if new_indicators:
        df = pd.concat([df, pd.DataFrame(new_indicators, index=df.index)], axis=1)

    decisions["gap_actions"] = gap_actions
    decisions["missing_indicator_cols"] = missing_indicator_cols
    decisions["n_rows"] = int(len(df))
    decisions["n_sensor_cols_kept"] = len(remaining)

    return df, decisions


def main():
    df = load_raw()
    cleaned, decisions = clean(df)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "sensor_handling.json").write_text(json.dumps(decisions, indent=2), encoding="utf-8")

    lines = [
        "# T09 — Sensor handling decisions (generated from data_cleaning.py)",
        "",
        f"Rows: {decisions['n_rows']} | Sensor columns kept: {decisions['n_sensor_cols_kept']}",
        "",
        "## Dropped",
        *(f"- `{k}`: {v}" for k, v in decisions["dropped"].items()),
        "",
        "## Gap handling (deviates from docs where long gaps were found — see module docstring)",
        "",
        "| Sensor | Action | Missing (min) | Longest gap (min) |",
        "|---|---|---:|---:|",
    ]
    for sensor, info in sorted(
        decisions["gap_actions"].items(), key=lambda kv: -kv[1]["longest_gap_min"]
    ):
        lines.append(
            f"| `{sensor}` | {info['action']} | {info['n_missing']} | {info['longest_gap_min']} |"
        )
    lines += [
        "",
        f"Short-gap interpolation threshold: {MAX_INTERP_GAP} min. Sensors whose longest "
        "gap exceeds this get a `_was_missing` indicator column instead of a filled value.",
        "",
        f"Missingness indicator columns added: {decisions['missing_indicator_cols']}",
    ]
    (REPORTS_DIR / "sensor_handling.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Cleaned shape: {cleaned.shape}")
    print(f"Wrote {REPORTS_DIR / 'sensor_handling.md'}")
    return cleaned, decisions


if __name__ == "__main__":
    main()
