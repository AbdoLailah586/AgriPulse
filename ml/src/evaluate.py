"""Shared event-level evaluation utilities (T23 in the plan, used from T14 onward).

Implements the metrics docs/ specifies in section 4.8: detection rate, lead time,
false-alarm rate — computed per held-out failure event, never averaged across the
7 events as if they were a large test set (there are only 7; report them individually).
"""

import numpy as np
import pandas as pd

from config import STATUS_COL, TS_COL
from validation import get_event_blocks


def threshold_from_normal(scores_normal: np.ndarray, percentile: float = 99.0) -> float:
    return float(np.nanpercentile(scores_normal, percentile))


def event_detection(
    df: pd.DataFrame,
    score_col: str,
    window_min: int,
    threshold: float,
    t_broken: pd.Timestamp,
    persist_n: int = 1,
) -> dict:
    """Did `score_col` cross `threshold` for >= persist_n consecutive rows inside
    this event's WARNING window, and if so, how many minutes before failure?"""
    window = pd.Timedelta(minutes=window_min)
    mask = (df[TS_COL] >= t_broken - window) & (df[TS_COL] < t_broken)
    sub = df.loc[mask, [TS_COL, score_col]].sort_values(TS_COL).reset_index(drop=True)

    above = (sub[score_col] >= threshold).to_numpy()
    run = 0
    first_qualifying_idx = None
    for i, v in enumerate(above):
        run = run + 1 if v else 0
        if run >= persist_n:
            first_qualifying_idx = i - persist_n + 1
            break

    if first_qualifying_idx is None:
        return {"detected": False, "lead_time_min": None}

    fire_ts = sub.loc[first_qualifying_idx, TS_COL]
    lead_time_min = (t_broken - fire_ts).total_seconds() / 60
    return {"detected": True, "lead_time_min": float(lead_time_min)}


def false_alarm_rate_per_week(
    df: pd.DataFrame,
    score_col: str,
    threshold: float,
    normal_mask: pd.Series,
    persist_n: int = 1,
) -> float:
    """Count distinct alert episodes (score >= threshold for >= persist_n rows,
    collapsing consecutive qualifying rows into one episode) per week of NORMAL
    operation time actually scored."""
    sub = df.loc[normal_mask].sort_values(TS_COL)
    above = (sub[score_col] >= threshold).to_numpy()

    run = 0
    episodes = 0
    in_episode = False
    for v in above:
        run = run + 1 if v else 0
        if run >= persist_n and not in_episode:
            episodes += 1
            in_episode = True
        if not v:
            run = 0
            in_episode = False

    n_minutes = len(sub)
    n_weeks = n_minutes / (60 * 24 * 7)
    return episodes / n_weeks if n_weeks > 0 else float("nan")


def evaluate_detector_per_event(
    df: pd.DataFrame,
    score_col: str,
    window_min: int,
    threshold: float,
    persist_n: int = 1,
) -> pd.DataFrame:
    """Event-level results for all 7 failures, using a single pre-fit threshold.
    Caller is responsible for ensuring `score_col` was produced by a model that
    never saw the corresponding held-out event during training (leave-one-failure-out).
    """
    blocks = get_event_blocks(df, window_min)
    rows = []
    for i, block in enumerate(blocks):
        res = event_detection(df, score_col, window_min, threshold, block["t_broken"], persist_n)
        rows.append({"event": i, "t_broken": block["t_broken"], **res})
    return pd.DataFrame(rows)
