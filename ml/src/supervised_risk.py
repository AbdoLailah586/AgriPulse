"""T16 — Supervised risk classifiers (XGBoost, LightGBM) on the T13 engineered
feature table, binary NORMAL-vs-WARNING per horizon, class-weighted (no
synthetic oversampling, per docs/). T17 — isotonic calibration of each model's
probability output, plus Green/Yellow/Orange/Red levels from the calibrated
NORMAL-training distribution. Evaluated leave-one-failure-out like T14/T15.

BUG FOUND AND FIXED during the first run: thresholding off the ISOTONIC-
CALIBRATED score degenerates when a class is this separable. NORMAL is ~98%
of training rows and the raw classifier already separates it near-perfectly
(mean raw proba ~6.5e-6 for NORMAL vs ~0.9999 for WARNING in-sample), so
isotonic regression collapses the entire NORMAL score range to calibrated
probability exactly 0.0 — including its 99th percentile. A threshold of
exactly 0.0 is then trivially satisfied by every row (probabilities can't go
negative), so detection fired at minute 1 of every window on every fold and
looked like a perfect 7/7 — purely a thresholding artifact, not a real
result. Fix: compute the alert threshold from each fold's RAW (uncalibrated)
probability distribution, which varies continuously and isn't pinned to a
repeated value; calibration is still reported per-row for interpretability
but is no longer used to pick the detection threshold.
"""

import json
import time

import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.isotonic import IsotonicRegression

from config import DEFAULT_WARNING_WINDOW_MIN, PROCESSED_DIR, REPORTS_DIR, STATUS_COL, TS_COL, WARNING_WINDOWS_MIN
from evaluate import evaluate_detector_per_event, false_alarm_rate_per_week, threshold_from_normal
from validation import leave_one_failure_out_splits

EXCLUDE_COLS = (
    {TS_COL, STATUS_COL}
    | {f"label_{w}" for w in WARNING_WINDOWS_MIN}
    | {f"rul_{w}" for w in WARNING_WINDOWS_MIN}
)


def feature_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in EXCLUDE_COLS]


def _risk_levels(calibrated_normal: np.ndarray) -> dict:
    """Green/Yellow/Orange/Red thresholds from the calibrated-probability
    distribution on training NORMAL data (per docs/ section 4.6)."""
    return {
        "yellow": float(np.percentile(calibrated_normal, 90)),
        "orange": float(np.percentile(calibrated_normal, 99)),  # also the alert/detection threshold
        "red": float(np.percentile(calibrated_normal, 99.9)),
    }


def run(window_min: int = DEFAULT_WARNING_WINDOW_MIN, persist_n: int = 15):
    t0 = time.time()
    df = pd.read_parquet(PROCESSED_DIR / "features_v1.parquet")
    cols = feature_cols(df)
    label_col = f"label_{window_min}"
    print(f"loaded {df.shape}, {len(cols)} features ({time.time() - t0:.0f}s)")

    results = {m: [] for m in ["xgboost", "lightgbm"]}
    far = {m: [] for m in results}
    risk_levels_per_fold = {m: [] for m in results}

    for fold_id, train_mask, val_mask in leave_one_failure_out_splits(df, window_min):
        train_sub = train_mask & df[label_col].isin(["NORMAL", "WARNING"])
        y = (df.loc[train_sub, label_col] == "WARNING").astype(int)
        X = df.loc[train_sub, cols]
        spw = (y == 0).sum() / max((y == 1).sum(), 1)

        xgb_model = xgb.XGBClassifier(
            n_estimators=150, max_depth=5, scale_pos_weight=spw, n_jobs=-1,
            tree_method="hist", eval_metric="aucpr", random_state=42,
        )
        xgb_model.fit(X, y)

        lgb_model = lgb.LGBMClassifier(
            n_estimators=150, max_depth=5, class_weight="balanced", n_jobs=-1,
            verbosity=-1, random_state=42,
        )
        lgb_model.fit(X, y)

        X_all = df[cols]
        raw_proba = {
            "xgboost": xgb_model.predict_proba(X_all)[:, 1],
            "lightgbm": lgb_model.predict_proba(X_all)[:, 1],
        }

        train_normal_mask = (train_mask & (df[label_col] == "NORMAL")).to_numpy()

        scored = df[[TS_COL, STATUS_COL, label_col]].copy()
        for m, raw in raw_proba.items():
            iso = IsotonicRegression(out_of_bounds="clip")
            iso.fit(raw[train_sub.to_numpy()], y.to_numpy())
            calibrated = iso.transform(raw)
            scored[f"{m}_calibrated"] = calibrated  # kept for interpretability only
            scored[m] = raw  # detection threshold is computed on the RAW score (see module docstring)

            thr = threshold_from_normal(raw[train_normal_mask], 99)
            bdf = evaluate_detector_per_event(scored, m, window_min, thr, persist_n)
            results[m].append({"fold": fold_id, "raw_threshold": thr, **bdf.iloc[fold_id].to_dict()})
            far[m].append(false_alarm_rate_per_week(scored, m, thr, pd.Series(train_normal_mask, index=df.index), persist_n))
            risk_levels_per_fold[m].append(_risk_levels(raw[train_normal_mask]))

        print(f"fold {fold_id} done ({time.time() - t0:.0f}s elapsed)")

    summary = {}
    for m in results:
        det = [r["detected"] for r in results[m]]
        leads = [r["lead_time_min"] for r in results[m] if pd.notna(r["lead_time_min"])]
        avg_levels = {
            k: float(np.mean([rl[k] for rl in risk_levels_per_fold[m]]))
            for k in ["yellow", "orange", "red"]
        }
        summary[m] = {
            "detection_rate": f"{sum(det)}/{len(det)}",
            "lead_time_min_mean": float(np.mean(leads)) if leads else None,
            "lead_time_min_median": float(np.median(leads)) if leads else None,
            "false_alarms_per_week_mean_insample": float(np.nanmean(far[m])),
            "risk_level_thresholds_mean_across_folds": avg_levels,
            "per_event": results[m],
        }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "t16_t17_supervised_risk.json"
    out.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({m: {k: v for k, v in s.items() if k != "per_event"} for m, s in summary.items()}, indent=2))
    print(f"Wrote {out} (total {time.time() - t0:.0f}s)")
    return summary


if __name__ == "__main__":
    run()
