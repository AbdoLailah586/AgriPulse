# AgriPulse — AI Predictive Maintenance for Irrigation Pumps

Graduation project, AI Engineering Program, Faculty of Engineering, Mansoura University.

Full plan: see [`docs/AI_Predictive_Maintenance_System_—_Full_Project_Documentation.pdf`](docs/AI_Predictive_Maintenance_System_—_Full_Project_Documentation.pdf)
(sequential task plan T01–T67) and [`docs/AgriPulse (1).pdf`](<docs/AgriPulse (1).pdf>) (thesis-format proposal).

## Layout (mirrors the plan's workstreams)

| Folder | Workstream |
|---|---|
| `ml/` | WS1 data & features, WS2 models, WS3 explainability & evaluation |
| `ml/models/v1/` | T20 production model artifacts + model card |
| `rag/` | WS4 knowledge base & RAG engine |
| `backend/` | WS6 API, auth, database |
| `frontend/` | WS8 dashboard |
| `iot/` | WS7 edge firmware |
| `data/raw/` | `sensor.csv` (gitignored — not committed, see below) |
| `docs/` | Source planning documents |

## Setup

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
```

## Data note

`data/raw/sensor.csv` (220,320 rows × 52 sensors, Apr–Aug 2018, `machine_status`
NORMAL/RECOVERING/BROKEN) is **not committed** — it's 124 MB and gitignored.
Validated against the plan's claims in `ml/reports/profile_report.json`
(run `ml/src/profile_dataset.py` to regenerate): row count, 7 breakdown
timestamps, and missingness per sensor all match exactly.

**Provenance TODO:** confirm and cite the dataset's actual public source before
submission — the structure (minute-level, zero gaps/duplicates across 5 months,
`sensor_00`..`sensor_51`, this exact `machine_status` scheme) matches a known
public Kaggle predictive-maintenance pump dataset rather than proprietary
Egyptian field telemetry. Doesn't block the engineering work, but the thesis
should cite the real source rather than imply it's original field data.

## Progress — WS1 (data & features)

| Task | Status | Output |
|---|---|---|
| T08 ingest & profile | done | `ml/reports/profile_report.json` |
| T09 clean & sensor handling | done | `ml/reports/sensor_handling.md` — **deviates from the plan docs**: sensor_50/51 have multi-day gaps overlapping breakdown events #7 and #5, so they're flagged (indicator column), not imputed as the docs suggested |
| T10 labeling (WARNING/RUL) | done | `ml/src/labeling.py`, windows 360/480/720 min |
| T11 leave-one-failure-out validation | done | `ml/src/validation.py`, 7 folds, 360min purge |
| T12 feature engineering | done | `ml/src/features.py` — rolling/EWM/FFT/cross-sensor |
| T13 versioned feature table | done | `data/processed/features_v1.parquet` (1053 cols, gitignored — regenerate with `ml/src/build_features.py`), dictionary in `ml/reports/data_dictionary.md` |
Run the pipeline: `cd ml/src && ../../.venv/Scripts/python build_features.py`

## Progress — WS2 (model training & evaluation)

All evaluated leave-one-failure-out (7 folds, one event held out per fold).

| Task | Status | Headline result | Output |
|---|---|---|---|
| T14 anomaly baselines (IsoForest/PCA/Mahalanobis) | done | 1–2/7 detected — honest, weak baselines | `ml/reports/t14_anomaly_baselines.json` |
| T15 LSTM-Autoencoder | done | 1/7 detected — first pass, 4 epochs, not tuned | `ml/reports/t15_lstm_autoencoder.json` |
| T16 supervised risk (XGBoost/LightGBM) | done | 3/7 detected — see bug note below | `ml/reports/t16_t17_supervised_risk.json` |
| T17 calibration + risk levels | done | isotonic + Green/Yellow/Orange/Red thresholds | same file |
| T18 persistence/hysteresis | done | self-tested: single spike absorbed, sustained rise escalates | `ml/src/alert_state.py` |
| T19 RUL regressor | done | MAE ~194min on a 720min horizon | `ml/reports/t19_rul_model.json` |
| T20 model registry + card | done | production artifacts trained on all 7 events | `ml/models/v1/model_card.json` |

**Bug caught and fixed:** T16/T17's first run reported a suspicious "perfect" 7/7
detection at full lead time on every fold. Root cause: isotonic calibration
collapsed the near-perfectly-separated NORMAL class to calibrated probability
exactly `0.0`, so the 99th-percentile alert threshold was also `0.0` — and since
probabilities can't go negative, every row trivially satisfied `score >= 0`. Fixed
by thresholding on the raw (uncalibrated) probability instead; re-run gives the
real 3/7 result above. See `ml/src/supervised_risk.py` docstring.

Run model training: `cd ml/src && ../../.venv/Scripts/python anomaly_baselines.py`
(similarly for `lstm_autoencoder.py`, `supervised_risk.py`, `rul_model.py`,
`model_registry.py`).
