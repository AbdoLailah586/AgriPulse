"""T19 — Remaining Useful Life (RUL) regressor: predicts minutes-to-failure for
rows already inside the WARNING window (target is undefined outside it — see
labeling.py). Evaluated with MAE plus an asymmetric score that penalizes
over-estimating RUL (predicted > actual, i.e. telling maintenance they have
more time than they really do — the dangerous direction) twice as heavily as
under-estimating it (predicted < actual — overly cautious, but safe).
"""

import json
import time

import numpy as np
import pandas as pd
import xgboost as xgb

from config import DEFAULT_WARNING_WINDOW_MIN, PROCESSED_DIR, REPORTS_DIR
from supervised_risk import feature_cols
from validation import leave_one_failure_out_splits

LATE_PENALTY_MULTIPLIER = 2.0  # over-prediction (false sense of safety) penalized 2x


def asymmetric_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    err = y_pred - y_true
    penalty = np.where(err > 0, err * LATE_PENALTY_MULTIPLIER, -err)
    return float(np.mean(penalty))


def run(window_min: int = DEFAULT_WARNING_WINDOW_MIN):
    t0 = time.time()
    df = pd.read_parquet(PROCESSED_DIR / "features_v1.parquet")
    cols = feature_cols(df)
    label_col = f"label_{window_min}"
    rul_col = f"rul_{window_min}"
    print(f"loaded {df.shape} ({time.time() - t0:.0f}s)")

    per_fold = []
    for fold_id, train_mask, val_mask in leave_one_failure_out_splits(df, window_min):
        train_rul = train_mask & (df[label_col] == "WARNING")
        val_rul = val_mask & (df[label_col] == "WARNING")

        if val_rul.sum() == 0:
            continue

        X_train, y_train = df.loc[train_rul, cols], df.loc[train_rul, rul_col].astype(float)
        X_val, y_val = df.loc[val_rul, cols], df.loc[val_rul, rul_col].astype(float)

        model = xgb.XGBRegressor(
            n_estimators=150, max_depth=5, n_jobs=-1, tree_method="hist", random_state=42
        )
        model.fit(X_train, y_train)
        pred = model.predict(X_val)

        mae = float(np.mean(np.abs(pred - y_val.to_numpy())))
        asym = asymmetric_score(y_val.to_numpy(), pred)
        per_fold.append(
            {
                "fold": fold_id,
                "n_val_rows": int(val_rul.sum()),
                "mae_min": mae,
                "asymmetric_score_min": asym,
                "mean_true_rul": float(y_val.mean()),
                "mean_pred_rul": float(pred.mean()),
            }
        )
        print(f"fold {fold_id}: MAE={mae:.1f}min asymmetric={asym:.1f}min ({time.time() - t0:.0f}s elapsed)")

    summary = {
        "label_horizon_min": window_min,
        "late_penalty_multiplier": LATE_PENALTY_MULTIPLIER,
        "mae_min_mean_across_folds": float(np.mean([f["mae_min"] for f in per_fold])),
        "asymmetric_score_min_mean_across_folds": float(np.mean([f["asymmetric_score_min"] for f in per_fold])),
        "per_fold": per_fold,
        "note": "Each fold's test set is one failure event's ~720 WARNING rows (highly "
        "autocorrelated, not independent samples) — treat as 7 event-level results, "
        "not a large statistically independent test set.",
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "t19_rul_model.json"
    out.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "per_fold"}, indent=2))
    print(f"Wrote {out}")
    return summary


if __name__ == "__main__":
    run()
