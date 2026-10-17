"""T20 — Train the production artifact (all 7 events, no held-out fold — the
leave-one-out folds in T14-T19 are for EVALUATION only) and package a single
predict() interface plus a model card, matching the plan's interface
contracts (docs/ section 3.7: prediction JSON = {pump_id, timestamp,
anomaly_score, risk_prob, level, rul_hours, top_sensors, model_version}).
"""

import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.preprocessing import StandardScaler

from config import DEFAULT_WARNING_WINDOW_MIN, PROCESSED_DIR, REPORTS_DIR, ROOT, SENSOR_PREFIX
from supervised_risk import _risk_levels, feature_cols

VERSION = "v1"
MODEL_DIR = ROOT / "ml" / "models" / VERSION


def _sensor_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith(SENSOR_PREFIX) and not c.endswith("_was_missing")]


def train_production_models(window_min: int = DEFAULT_WARNING_WINDOW_MIN):
    t0 = time.time()
    df = pd.read_parquet(PROCESSED_DIR / "features_v1.parquet")
    label_col = f"label_{window_min}"
    rul_col = f"rul_{window_min}"
    cols = feature_cols(df)

    # Risk classifier: all NORMAL + WARNING rows from all 7 events (deployment
    # model — unlike T16's evaluation folds, nothing is held out here).
    sub = df[df[label_col].isin(["NORMAL", "WARNING"])]
    y = (sub[label_col] == "WARNING").astype(int)
    X = sub[cols]
    spw = (y == 0).sum() / max((y == 1).sum(), 1)

    print(f"training production risk classifier on {len(X)} rows, {len(cols)} features ({time.time()-t0:.0f}s)")
    risk_model = xgb.XGBClassifier(
        n_estimators=150, max_depth=5, scale_pos_weight=spw, n_jobs=-1,
        tree_method="hist", eval_metric="aucpr", random_state=42,
    )
    risk_model.fit(X, y)

    raw_all = risk_model.predict_proba(df[cols])[:, 1]
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(raw_all[(df[label_col].isin(["NORMAL", "WARNING"])).to_numpy()], y.to_numpy())

    normal_mask = (df[label_col] == "NORMAL").to_numpy()
    risk_levels = _risk_levels(raw_all[normal_mask])

    # RUL regressor: all WARNING rows from all 7 events.
    rul_sub = df[df[label_col] == "WARNING"]
    print(f"training production RUL regressor on {len(rul_sub)} rows ({time.time()-t0:.0f}s)")
    rul_model = xgb.XGBRegressor(n_estimators=150, max_depth=5, n_jobs=-1, tree_method="hist", random_state=42)
    rul_model.fit(rul_sub[cols], rul_sub[rul_col].astype(float))

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(risk_model, MODEL_DIR / "risk_classifier_xgb.joblib")
    joblib.dump(iso, MODEL_DIR / "risk_calibrator_isotonic.joblib")
    joblib.dump(rul_model, MODEL_DIR / "rul_regressor_xgb.joblib")
    (MODEL_DIR / "feature_list.json").write_text(json.dumps(cols), encoding="utf-8")
    (MODEL_DIR / "risk_thresholds.json").write_text(json.dumps(risk_levels, indent=2), encoding="utf-8")

    print(f"Saved artifacts to {MODEL_DIR} ({time.time()-t0:.0f}s total)")
    return {
        "version": VERSION,
        "window_min": window_min,
        "n_features": len(cols),
        "risk_thresholds": risk_levels,
        "train_rows_risk": int(len(X)),
        "train_rows_rul": int(len(rul_sub)),
    }


def write_model_card(training_summary: dict):
    report_files = {
        "t14_anomaly_baselines": "t14_anomaly_baselines.json",
        "t15_lstm_autoencoder": "t15_lstm_autoencoder.json",
        "t16_t17_supervised_risk": "t16_t17_supervised_risk.json",
        "t19_rul_model": "t19_rul_model.json",
    }
    eval_summary = {}
    for key, fname in report_files.items():
        path = REPORTS_DIR / fname
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            eval_summary[key] = {k: v for k, v in data.items() if k not in ("per_event", "per_fold")}
        else:
            eval_summary[key] = "not yet run"

    card = {
        "model_version": training_summary["version"],
        "intended_use": "Early-warning risk scoring and maintenance work-order triggering for the "
        "AgriPulse pump telemetry demo dataset. NOT validated on a different pump, sensor set, or "
        "site — see docs/ provenance note before any claim of field readiness.",
        "training_data": "sensor.csv, 220,320 rows, 7 failure events (same 7 events used for both "
        "training this production artifact and the leave-one-failure-out evaluation below — "
        "evaluation folds hold out one event at a time; THIS artifact uses all 7, so its own "
        "training-set performance is not a valid estimate of its generalization — refer to the "
        "leave-one-failure-out numbers for that).",
        "known_limitations": [
            "Only 7 failure events total — every evaluation number below is a single-event result, "
            "not large-sample statistics.",
            "sensor_50/sensor_51 have multi-day gaps overlapping breakdown events #7 and #5 — see "
            "ml/reports/sensor_handling.md.",
            "T16/T17 first run had a threshold-calibration bug (isotonic calibration collapsed the "
            "NORMAL class to probability 0.0, making the 99th-percentile alert threshold also 0.0, "
            "which trivially fired on every row) — fixed by thresholding on raw, not calibrated, "
            "probability. See supervised_risk.py docstring.",
        ],
        "evaluation_leave_one_failure_out": eval_summary,
        "artifacts": training_summary,
        "generated_from": "ml/src/model_registry.py",
    }

    (MODEL_DIR / "model_card.json").write_text(json.dumps(card, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {MODEL_DIR / 'model_card.json'}")
    return card


if __name__ == "__main__":
    summary = train_production_models()
    write_model_card(summary)
