"""T15 — LSTM-Autoencoder anomaly detector: the primary detector per docs/
section 4.5, trained exclusively on NORMAL sequences. Reconstruction error
(MSE) is the anomaly score; per-sensor error is a first explanation (feeds T21
SHAP/explainability work later).

Scope note: CPU-only training (no GPU in this environment). Sequences are
strided (not every minute) to keep 7-fold training tractable — documented
here rather than silently capped. This is a first working pass with modest
architecture/epochs; hyperparameter tuning is a follow-up, not done here.
"""

import json
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from config import DEFAULT_WARNING_WINDOW_MIN, PROCESSED_DIR, REPORTS_DIR, SENSOR_PREFIX, STATUS_COL, TS_COL
from evaluate import evaluate_detector_per_event, false_alarm_rate_per_week, threshold_from_normal
from validation import leave_one_failure_out_splits

SEQ_LEN = 30  # minutes of context per sequence
STRIDE = 5  # training sequence stride (subsample — adjacent 1-min sequences are near-duplicates)
HIDDEN = 32
EPOCHS = 4
BATCH_SIZE = 256
LR = 1e-3


class LSTMAutoencoder(nn.Module):
    def __init__(self, n_features: int, hidden: int = HIDDEN):
        super().__init__()
        self.encoder = nn.LSTM(n_features, hidden, batch_first=True)
        self.decoder = nn.LSTM(hidden, hidden, batch_first=True)
        self.output = nn.Linear(hidden, n_features)

    def forward(self, x):
        _, (h, c) = self.encoder(x)
        seq_len = x.size(1)
        h_rep = h.permute(1, 0, 2).repeat(1, seq_len, 1)
        dec_out, _ = self.decoder(h_rep)
        return self.output(dec_out)


def _sensor_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith(SENSOR_PREFIX) and not c.endswith("_was_missing")]


def _make_sequences(X: np.ndarray, seq_len: int, stride: int) -> np.ndarray:
    n = len(X)
    starts = range(0, n - seq_len + 1, stride)
    return np.stack([X[s : s + seq_len] for s in starts])


def train_one_fold(X_train: np.ndarray, n_features: int) -> LSTMAutoencoder:
    seqs = _make_sequences(X_train, SEQ_LEN, STRIDE)
    tensor = torch.tensor(seqs, dtype=torch.float32)

    model = LSTMAutoencoder(n_features)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    loss_fn = nn.MSELoss()

    n = len(tensor)
    for epoch in range(EPOCHS):
        perm = torch.randperm(n)
        total_loss = 0.0
        for i in range(0, n, BATCH_SIZE):
            batch = tensor[perm[i : i + BATCH_SIZE]]
            opt.zero_grad()
            recon = model(batch)
            loss = loss_fn(recon, batch)
            loss.backward()
            opt.step()
            total_loss += loss.item() * len(batch)
        print(f"    epoch {epoch + 1}/{EPOCHS} loss={total_loss / n:.4f}")
    return model


def score_all(model: LSTMAutoencoder, X: np.ndarray) -> np.ndarray:
    """Per-minute anomaly score = reconstruction MSE of the trailing SEQ_LEN window
    ending at that minute (every minute scored — unlike training, no stride)."""
    model.eval()
    n, n_features = X.shape
    scores = np.full(n, np.nan)
    with torch.no_grad():
        for start in range(0, n - SEQ_LEN + 1, 2000):  # chunked for memory
            end = min(start + 2000, n - SEQ_LEN + 1)
            batch_seqs = np.stack([X[s : s + SEQ_LEN] for s in range(start, end)])
            batch = torch.tensor(batch_seqs, dtype=torch.float32)
            recon = model(batch).numpy()
            mse = np.mean((batch_seqs - recon) ** 2, axis=(1, 2))
            scores[start + SEQ_LEN - 1 : end + SEQ_LEN - 1] = mse
    return scores


def run(window_min: int = DEFAULT_WARNING_WINDOW_MIN, persist_n: int = 15):
    t0 = time.time()
    df = pd.read_parquet(PROCESSED_DIR / "labeled.parquet")
    cols = _sensor_cols(df)
    label_col = f"label_{window_min}"
    n_features = len(cols)

    results = []
    far = []

    for fold_id, train_mask, val_mask in leave_one_failure_out_splits(df, window_min):
        train_normal = train_mask & (df[label_col] == "NORMAL")

        imputer = SimpleImputer(strategy="median")
        scaler = StandardScaler()
        X_train = scaler.fit_transform(imputer.fit_transform(df.loc[train_normal, cols]))

        print(f"fold {fold_id}: training on {len(X_train)} normal rows ({time.time() - t0:.0f}s elapsed)")
        model = train_one_fold(X_train, n_features)

        X_all = scaler.transform(imputer.transform(df[cols]))
        scores = score_all(model, X_all)

        scored = df[[TS_COL, STATUS_COL, label_col]].copy()
        scored["lstm_ae"] = scores

        train_scores = scores[train_normal.to_numpy()]
        threshold = threshold_from_normal(train_scores[~np.isnan(train_scores)], 99)

        bdf = evaluate_detector_per_event(scored, "lstm_ae", window_min, threshold, persist_n)
        results.append({"fold": fold_id, **bdf.iloc[fold_id].to_dict()})
        far.append(false_alarm_rate_per_week(scored, "lstm_ae", threshold, train_normal, persist_n))

        print(f"  -> fold {fold_id} done ({time.time() - t0:.0f}s elapsed): {results[-1]}")

    det = [r["detected"] for r in results]
    leads = [r["lead_time_min"] for r in results if pd.notna(r["lead_time_min"])]
    summary = {
        "architecture": f"LSTM-AE seq_len={SEQ_LEN} hidden={HIDDEN} epochs={EPOCHS} stride={STRIDE}",
        "detection_rate": f"{sum(det)}/{len(det)}",
        "lead_time_min_mean": float(np.mean(leads)) if leads else None,
        "lead_time_min_median": float(np.median(leads)) if leads else None,
        "false_alarms_per_week_mean_insample": float(np.nanmean(far)),
        "per_event": results,
        "total_runtime_sec": time.time() - t0,
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "t15_lstm_autoencoder.json"
    out.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "per_event"}, indent=2))
    print(f"Wrote {out}")
    return summary


if __name__ == "__main__":
    run()
