# AgriPulse — AI Predictive Maintenance for Irrigation Pumps

Graduation project, AI Engineering Program, Faculty of Engineering, Mansoura University.

Full plan: see [`docs/AI_Predictive_Maintenance_System_—_Full_Project_Documentation.pdf`](docs/AI_Predictive_Maintenance_System_—_Full_Project_Documentation.pdf)
(sequential task plan T01–T67) and [`docs/AgriPulse (1).pdf`](<docs/AgriPulse (1).pdf>) (thesis-format proposal).

## Layout (mirrors the plan's workstreams)

| Folder | Workstream |
|---|---|
| `ml/` | WS1 data & features, WS2 models, WS3 explainability & evaluation |
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
| T14+ (model training) | not started | next up |

Run the pipeline: `cd ml/src && ../../.venv/Scripts/python build_features.py`
