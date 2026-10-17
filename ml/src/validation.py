"""T11 — Leave-one-failure-out validation splits with a purge gap.

Each of the 7 failure events becomes one fold: its WARNING+BROKEN window (plus
some NORMAL context before it) is held out for validation, the matching
RECOVERING tail is excluded from both train and val entirely (per docs/: it's
neither a normal nor a pre-failure state, so it isn't a useful training or
eval target), and a purge gap (>= longest rolling feature window, see
config.PURGE_MIN) is cut out of training on both sides of the held-out block
to stop adjacent rolling-window features leaking fold information.
"""

import numpy as np
import pandas as pd

from config import PURGE_MIN, STATUS_COL, TS_COL


def _recovering_block_end(df: pd.DataFrame, broken_pos: int) -> pd.Timestamp:
    """Walk forward from a BROKEN row while status stays RECOVERING."""
    status = df[STATUS_COL].to_numpy()
    ts = df[TS_COL].to_numpy()
    i = broken_pos + 1
    n = len(status)
    while i < n and status[i] == "RECOVERING":
        i += 1
    return ts[i - 1] if i > broken_pos + 1 else ts[broken_pos]


def get_event_blocks(df: pd.DataFrame, window_min: int) -> list[dict]:
    broken_positions = np.flatnonzero((df[STATUS_COL] == "BROKEN").to_numpy())
    window = pd.Timedelta(minutes=window_min)
    blocks = []
    for pos in broken_positions:
        t_broken = df[TS_COL].iloc[pos]
        rec_end = _recovering_block_end(df, pos)
        blocks.append(
            {
                "t_broken": t_broken,
                "val_start": t_broken - window,  # start of WARNING horizon
                "val_end": rec_end,  # end of this event's RECOVERING tail
            }
        )
    return blocks


def leave_one_failure_out_splits(df: pd.DataFrame, window_min: int, purge_min: int = PURGE_MIN):
    """Yield (fold_id, train_mask, val_mask) boolean Series, one per failure event.

    val_mask: NORMAL/WARNING/BROKEN rows inside this event's held-out block.
    train_mask: NORMAL/WARNING/BROKEN rows from every OTHER event, excluding a
    purge buffer around the held-out block. RECOVERING rows are never in
    either mask.
    """
    blocks = get_event_blocks(df, window_min)
    not_recovering = df[STATUS_COL] != "RECOVERING"
    purge = pd.Timedelta(minutes=purge_min)

    for fold_id, block in enumerate(blocks):
        in_block = (df[TS_COL] >= block["val_start"]) & (df[TS_COL] <= block["val_end"])
        val_mask = in_block & not_recovering

        in_purged_zone = (df[TS_COL] >= block["val_start"] - purge) & (
            df[TS_COL] <= block["val_end"] + purge
        )
        train_mask = (~in_purged_zone) & not_recovering

        yield fold_id, train_mask, val_mask


def main():
    from config import DEFAULT_WARNING_WINDOW_MIN, PROCESSED_DIR

    df = pd.read_parquet(PROCESSED_DIR / "labeled.parquet")

    for fold_id, train_mask, val_mask in leave_one_failure_out_splits(
        df, DEFAULT_WARNING_WINDOW_MIN
    ):
        label_col = f"label_{DEFAULT_WARNING_WINDOW_MIN}"
        val_counts = df.loc[val_mask, label_col].value_counts().to_dict()
        print(
            f"fold {fold_id}: train={int(train_mask.sum())} rows, "
            f"val={int(val_mask.sum())} rows {val_counts}"
        )


if __name__ == "__main__":
    main()
