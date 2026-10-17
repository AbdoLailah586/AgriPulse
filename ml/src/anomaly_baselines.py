"""T14 — Baseline anomaly detectors (Isolation Forest, PCA reconstruction error,
Mahalanobis distance), trained on NORMAL data only, evaluated per leave-one-
failure-out fold (7 events). These are comparison baselines for the LSTM-
Autoencoder (T15) — same input representation: cleaned sensor channels, not the
T12 engineered feature table (keeps this an apples-to-apples "raw channel
anomaly detection" comparison, per docs/ section 4.5).

Caveat (see evaluate.py): false-alarm rate here is computed on each fold's
TRAINING normal data (in-sample / optimistic) — with only 7 failure events and
no spare normal period held out, a clean out-of-sample false-alarm estimate
isn't available from this dataset. Detection rate and lead time ARE out-of-
sample (model and threshold never see the held-out event).
"""

import json

import numpy as np
import pandas as pd
from sklearn.covariance import EmpiricalCovariance
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from config import DEFAULT_WARNING_WINDOW_MIN, PROCESSED_DIR, REPORTS_DIR, SENSOR_PREFIX, STATUS_COL, TS_COL
from evaluate import evaluate_detector_per_event, false_alarm_rate_per_week, threshold_from_normal
from validation import leave_one_failure_out_splits


def _sensor_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith(SENSOR_PREFIX) and not c.endswith("_was_missing")]


def _fit_scorers(X_train: np.ndarray):
    iso = IsolationForest(n_estimators=200, contamination="auto", random_state=42, n_jobs=-1)
    iso.fit(X_train)

    pca = PCA(n_components=0.95, random_state=42)
    pca.fit(X_train)

    maha = EmpiricalCovariance()
    maha.fit(X_train)

    return iso, pca, maha


def _score(iso, pca, maha, X: np.ndarray) -> dict:
    iso_score = -iso.score_samples(X)  # higher = more anomalous
    recon = pca.inverse_transform(pca.transform(X))
    pca_score = np.mean((X - recon) ** 2, axis=1)
    maha_score = maha.mahalanobis(X)
    return {"isoforest": iso_score, "pca_recon": pca_score, "mahalanobis": maha_score}


def run(window_min: int = DEFAULT_WARNING_WINDOW_MIN, persist_n: int = 15):
    df = pd.read_parquet(PROCESSED_DIR / "labeled.parquet")
    cols = _sensor_cols(df)
    label_col = f"label_{window_min}"

    results = {m: [] for m in ["isoforest", "pca_recon", "mahalanobis"]}
    far = {m: [] for m in results}

    for fold_id, train_mask, val_mask in leave_one_failure_out_splits(df, window_min):
        train_normal = train_mask & (df[label_col] == "NORMAL")

        imputer = SimpleImputer(strategy="median")
        scaler = StandardScaler()
        X_train = scaler.fit_transform(imputer.fit_transform(df.loc[train_normal, cols]))

        iso, pca, maha = _fit_scorers(X_train)

        X_all = scaler.transform(imputer.transform(df[cols]))
        scores = _score(iso, pca, maha, X_all)

        scored = df[[TS_COL, STATUS_COL, label_col]].copy()
        for m, s in scores.items():
            scored[m] = s

        thresholds = {m: threshold_from_normal(scores[m][train_normal.to_numpy()], 99) for m in scores}

        blocks_df = evaluate_detector_per_event(
            scored, "isoforest", window_min, thresholds["isoforest"], persist_n
        )
        event_row = blocks_df.iloc[fold_id]
        results["isoforest"].append({"fold": fold_id, **event_row.to_dict()})

        for m in ["pca_recon", "mahalanobis"]:
            bdf = evaluate_detector_per_event(scored, m, window_min, thresholds[m], persist_n)
            results[m].append({"fold": fold_id, **bdf.iloc[fold_id].to_dict()})

        for m in scores:
            far[m].append(
                false_alarm_rate_per_week(scored, m, thresholds[m], train_normal, persist_n)
            )

    summary = {}
    for m in results:
        det = [r["detected"] for r in results[m]]
        leads = [r["lead_time_min"] for r in results[m] if pd.notna(r["lead_time_min"])]
        summary[m] = {
            "detection_rate": f"{sum(det)}/{len(det)}",
            "lead_time_min_mean": float(np.mean(leads)) if leads else None,
            "lead_time_min_median": float(np.median(leads)) if leads else None,
            "false_alarms_per_week_mean_insample": float(np.nanmean(far[m])),
            "per_event": results[m],
        }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "t14_anomaly_baselines.json"
    out.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({m: {k: v for k, v in s.items() if k != "per_event"} for m, s in summary.items()}, indent=2))
    print(f"Wrote {out}")
    return summary


if __name__ == "__main__":
    run()
