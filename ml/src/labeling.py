"""T10 — Pre-failure WARNING labels and RUL targets (configurable window length).

Label(t) precedence: BROKEN > WARNING > RECOVERING > NORMAL, matching the
formula in docs/ (section 4.2 / Chapter 4). RUL (minutes remaining until
failure) is only defined inside the WARNING window and at the BROKEN row
itself — outside that horizon "time to failure" isn't a meaningful target.
"""

import pandas as pd

from config import STATUS_COL, TS_COL, WARNING_WINDOWS_MIN


def add_labels(df: pd.DataFrame, window_min: int) -> pd.DataFrame:
    df = df.copy()
    broken_ts = df.loc[df[STATUS_COL] == "BROKEN", TS_COL]

    label_col = f"label_{window_min}"
    rul_col = f"rul_{window_min}"

    df[label_col] = "NORMAL"
    df.loc[df[STATUS_COL] == "RECOVERING", label_col] = "RECOVERING"

    df[rul_col] = pd.NA

    window = pd.Timedelta(minutes=window_min)
    for t_broken in broken_ts:
        in_warning = (df[TS_COL] >= t_broken - window) & (df[TS_COL] < t_broken)
        df.loc[in_warning, label_col] = "WARNING"
        rul_minutes = (t_broken - df.loc[in_warning, TS_COL]).dt.total_seconds() / 60
        df.loc[in_warning, rul_col] = rul_minutes.astype(int)

    df.loc[df[STATUS_COL] == "BROKEN", label_col] = "BROKEN"
    df.loc[df[STATUS_COL] == "BROKEN", rul_col] = 0

    return df


def add_all_label_windows(df: pd.DataFrame) -> pd.DataFrame:
    for w in WARNING_WINDOWS_MIN:
        df = add_labels(df, w)
    return df


def main():
    from config import PROCESSED_DIR
    from data_cleaning import clean, load_raw

    raw = load_raw()
    cleaned, _ = clean(raw)
    labeled = add_all_label_windows(cleaned)

    for w in WARNING_WINDOWS_MIN:
        counts = labeled[f"label_{w}"].value_counts()
        print(f"window={w}min ->", counts.to_dict())

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "labeled.parquet"
    labeled.to_parquet(out_path)
    print(f"Wrote {out_path} shape={labeled.shape}")


if __name__ == "__main__":
    main()
