"""T12 — Shared feature engineering library (used identically in training and serving).

Implements the four families from docs/ section 4.4:
  1. rolling time-domain stats (mean, std, min, max, range, skew) over multiple windows
  2. EWM (fast-reacting trend)
  3. FFT spectral features (dominant frequency, spectral energy) for a sensor subset
  4. correlation-based sensor grouping (neutral group labels — sensor semantics are
     anonymized, so physical names from docs/ are a hypothesis, not ground truth)
"""

import numpy as np
import pandas as pd

from config import EWM_SPAN_MIN, FFT_CANDIDATE_SENSORS, FFT_WINDOW_MIN, ROLLING_WINDOWS_MIN


def rolling_features(df: pd.DataFrame, cols: list[str], windows_min: list[int] = ROLLING_WINDOWS_MIN) -> pd.DataFrame:
    out = {}
    for w in windows_min:
        roll = df[cols].rolling(window=w, min_periods=max(2, w // 3))
        agg = roll.agg(["mean", "std", "min", "max", "skew"])
        for col in cols:
            out[f"{col}_roll{w}_mean"] = agg[(col, "mean")]
            out[f"{col}_roll{w}_std"] = agg[(col, "std")]
            out[f"{col}_roll{w}_min"] = agg[(col, "min")]
            out[f"{col}_roll{w}_max"] = agg[(col, "max")]
            out[f"{col}_roll{w}_range"] = agg[(col, "max")] - agg[(col, "min")]
            out[f"{col}_roll{w}_skew"] = agg[(col, "skew")]
    return pd.DataFrame(out, index=df.index)


def ewm_features(df: pd.DataFrame, cols: list[str], span_min: int = EWM_SPAN_MIN) -> pd.DataFrame:
    out = {f"{col}_ewm{span_min}_mean": df[col].ewm(span=span_min, min_periods=2).mean() for col in cols}
    return pd.DataFrame(out, index=df.index)


def _dominant_freq_and_energy(x: np.ndarray) -> tuple[float, float]:
    x = x[~np.isnan(x)]
    if len(x) < 4:
        return np.nan, np.nan
    x = x - x.mean()
    spectrum = np.abs(np.fft.rfft(x))
    if len(spectrum) <= 1:
        return 0.0, float(np.sum(spectrum**2))
    dominant_idx = int(np.argmax(spectrum[1:]) + 1)  # skip DC component
    energy = float(np.sum(spectrum**2))
    return float(dominant_idx), energy


def fft_features(
    df: pd.DataFrame,
    cols: list[str] = FFT_CANDIDATE_SENSORS,
    window_min: int = FFT_WINDOW_MIN,
) -> pd.DataFrame:
    """Rolling spectral features. Expensive (Python callback per window) — restricted
    to a small hypothesized vibration/current sensor subset per config.py, not all 52."""
    out = {}
    for col in cols:
        if col not in df.columns:
            continue
        dom_freq = np.full(len(df), np.nan)
        energy = np.full(len(df), np.nan)
        values = df[col].to_numpy()
        for i in range(window_min - 1, len(df)):
            window = values[i - window_min + 1 : i + 1]
            d, e = _dominant_freq_and_energy(window)
            dom_freq[i] = d
            energy[i] = e
        out[f"{col}_fft{window_min}_dominant_bin"] = dom_freq
        out[f"{col}_fft{window_min}_energy"] = energy
    return pd.DataFrame(out, index=df.index)


def sensor_groups(df: pd.DataFrame, cols: list[str], corr_threshold: float = 0.8) -> dict[str, list[str]]:
    """Cluster sensors into neutral groups by correlation (union-find on a threshold
    graph) — no scipy dependency. Labeled group_0, group_1, ... since sensor physical
    identity is anonymized; cross-reference docs/ sensor taxonomy as a hypothesis only."""
    corr = df[cols].corr().abs()
    parent = {c: c for c in cols}

    def find(c):
        while parent[c] != c:
            parent[c] = parent[parent[c]]
            c = parent[c]
        return c

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i, a in enumerate(cols):
        for b in cols[i + 1 :]:
            if corr.loc[a, b] >= corr_threshold:
                union(a, b)

    groups: dict[str, list[str]] = {}
    for c in cols:
        root = find(c)
        groups.setdefault(root, []).append(c)

    return {f"group_{i}": members for i, members in enumerate(groups.values()) if len(members) > 1}


def cross_sensor_ratio_features(df: pd.DataFrame, groups: dict[str, list[str]]) -> pd.DataFrame:
    """Within each correlated group, add pairwise ratios for the two lowest-missingness
    members (cheap, interpretable cross-sensor signal; full pairwise blows up fast)."""
    out = {}
    for gname, members in groups.items():
        if len(members) < 2:
            continue
        a, b = members[0], members[1]
        denom = df[b].replace(0, np.nan)
        out[f"{gname}_{a}_over_{b}"] = df[a] / denom
    return pd.DataFrame(out, index=df.index)
