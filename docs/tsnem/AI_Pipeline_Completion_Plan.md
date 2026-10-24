# AI System — Complete Pipeline & Completion Plan

> **Target Asset:** Industrial End-Suction Centrifugal Irrigation Pump (Standard: Grundfos NB / Kirloskar DB Series)
> **Document Purpose:** Engineering roadmap connecting model finalization, microservices, RAG, and physical test bench.
> **Version:** 2.0 — Standardized Architecture
> **Audience:** AI Team, Backend Team, Frontend Team

---

## Part 1 — Where We Are Now (Notebook State)

```mermaid
flowchart LR
    C1["Cell 1\nLoad Telemetry\n✅ Done"] --> C2["Cell 2\nCausal Impute\n✅ Done"]
    C2 --> C3["Cell 3\nFeature Eng (Core 7)\n✅ Done"]
    C3 --> C4["Cell 4\nTarget 120-min Window\n✅ Done"]
    C4 --> C5["Cell 5\nTrain + Dual Thresholds\n✅ Done"]
    C5 --> C6["Cell 6\nWalk-Forward\n⚠️ Minor fix (t_te)"]
    C6 --> C7["Cell 7\nSimulate 180 min\n⚠️ Minor fix (window)"]
    C7 --> C8["Cell 8\nExport JSON & PKL\n✅ Done"]
```

### Pending Notebook Fixes (Both Minor & Non-Breaking)

| Cell | Issue | Action Required |
| :--- | :--- | :--- |
| **Cell 6** | `d_te` references potentially lingering `t_te_end` | Replace with direct slice `d_te = clean_df[(clean_df["timestamp"] >= t_cal) & (clean_df["timestamp"] <= t_te)].copy().reset_index(drop=True)` |
| **Cell 7** | Simulation window is 90 mins (insufficient for 61-min warm-up + full 120-min failure window) | Change `pd.Timedelta(minutes=90)` to `pd.Timedelta(minutes=180)` |

---

## Part 2 — Full Production Architecture (Unified Gateway & Event Bus)

```mermaid
flowchart TD
    subgraph Edge ["Target Asset & Hardware Test Rig"]
        PUMP["End-Suction Centrifugal Irrigation Pump\n(Test Bench or Field Installation)"]
        ESP["ESP32 Telemetry Gateway\n5-8 Sensors (1 packet/min)\nADXL345, SCT-013, DS18B20, G1/4"]
        PUMP --> ESP
    end

    subgraph Backend ["Cloud Backend (Unified Gateway & AI Mesh)"]
        GW["Unified Ingress & API Gateway (FastAPI:8000)\n- REST API (/api/v1/*)\n- WebSocket (/ws/telemetry & /ws/alerts)"]
        BUS[("Redis 7 Event Bus\nPub/Sub & State Cache\ntelemetry:raw | scored | alerts")]
        DB[("PostgreSQL 16 + TimescaleDB\nHypertables: sensor_telemetry\nTables: weibull_predictions, alerts, work_orders")]
        INF["Causal ML Engine (Internal Service)\nStrictPumpRealTimeEngine + ExtraTrees\nWeibull RUL Regression"]
        RAG["RAG Assistant (Internal Service)\nChromaDB + Centrifugal Pump FMEA & Manuals\nAuto Work Order & LOTO Generator"]
        YOLO["Field Vision Engine (YOLOv8)\nFoliar Stress & Agro-Hydraulic Correlator"]
    end

    subgraph Frontend ["Frontend UI (React 18 / Vite)"]
        FE["React 18 Web Dashboard\nReal-time Health Gauge & Work Orders\nConnects to Port 8000"]
    end

    ESP -->|"HTTPS POST /api/v1/telemetry/ingest"| GW
    GW -->|"1. Store Raw Hypertable"| DB
    GW -->|"2. Publish 'telemetry:raw'"| BUS
    BUS -->|"3. Stream to Engine"| INF
    INF -->|"4. Save Predictions"| DB
    INF -->|"5. Publish 'telemetry:scored'"| BUS
    BUS -->|"6. On Score >= Warning/Critical"| RAG
    RAG -->|"7. Insert Work Order & LOTO"| DB
    YOLO -.->|"Agro-Hydraulic Query"| GW
    BUS -->|"8. Live Broadcast"| GW
    GW -->|"9. WebSocket Sub-Second Push"| FE
    FE -->|"10. REST API Calls (/api/v1/*)"| GW
```

---

## Part 3 — Core System Implementation & Internal Mesh

### 3.1 Unified API Gateway (Port 8000)
Exposes a single authenticated boundary for the React 18 Frontend and IoT edge devices:
- Handles `/api/v1/*` routes: telemetry ingestion, pump registry, predictive intelligence, alerts, work orders, assistant, and computer vision.
- Manages authenticated WebSockets (`/ws/telemetry` & `/ws/alerts`) connected to the Redis event bus.

### 3.2 Causal ML & Prognostics Engine (Internal Worker / Service)
Contains the exact serialized pipeline trained in the notebook:
- **Model:** `pump_engine_strict.pkl` (ExtraTrees Classifier trained on Core 7 sensors).
- **Prognostics:** Weibull Remaining Useful Life (RUL) regression ($\beta$ shape, $\eta$ scale).
- **Configuration:** `model_config.json` containing:
  - Warning Threshold: `0.2713`
  - Critical Threshold: `0.3169`
  - Core Sensor Set: `["sensor_00", "sensor_04", "sensor_05", "sensor_11", "sensor_13", "sensor_28", "sensor_40"]`
- **Memory Buffer:** Maintains a 65-reading rolling FIFO window per pump ID.
- **Warm-Up:** First 61 minutes report status `INITIALIZING` to build stable 15-min and 60-min trend baselines.

### 3.3 RAG Assistant & FMEA Knowledge Base (Internal Service)
Contains the pump-specific maintenance knowledge base:
- **Standards:** ISO 10816-3 (Vibration Severity for Class II Pumps), ANSI/HI 9.6 (Centrifugal Pumps), IEC 60034-1.
- **Manuals:** Standard Centrifugal Irrigation Pump Operation & Maintenance Manuals (Grundfos NB, Kirloskar DB).
- **FMEA Tables:**
  - Coupling Misalignment & Spider Wear (`sensor_13`).
  - Bearing Lubrication Starvation & Ball Defect (`sensor_00`, `sensor_40`).
  - Impeller Clogging & Motor Current Overload (`sensor_05`, `sensor_11`).
  - Hydraulic Cavitation & Suction Strainer Blockage (`sensor_28`, `sensor_48`).
- **Autonomous Trigger:** Subscribes to `alerts:trigger` on Redis to auto-synthesize Work Orders with LOTO checklists directly into PostgreSQL.

### 3.4 Field Vision & Agro-Hydraulic Correlator (Internal Service)
- YOLOv8 foliar pathology scans correlated with live pump discharge pressure (`sensor_48`) and flow rate (`sensor_28`) to distinguish pump failure from plant biological disease.

---

## Part 4 — Step-by-Step Execution Plan

| Stage | Task | Deliverable |
| :---: | :--- | :--- |
| **Phase 1** | Apply minor fixes in Cells 6 & 7 in Kaggle; run **Restart & Run All** | Verified `pump_engine_strict.pkl` & `model_config.json` |
| **Phase 2** | Initialize `inference-service` repo with Dockerfile & FastAPI wrapper | Live `/predict` endpoint on Railway |
| **Phase 3** | Initialize `ingestion-api` repo with PostgreSQL schemas | Database tables for telemetry & alerts |
| **Phase 4** | Build `rag-assistant` with ChromaDB vector store + FMEA markdown chunks | Automated Work Order generation on WARNING/CRITICAL |
| **Phase 5** | Connect ESP32 Hardware Prototype to Ingestion endpoint | Real physical telemetry flowing into the AI engine |
| **Phase 6** | End-to-end rehearsal with Replay Stream Script | 6-minute live simulation of Event 6 for defense presentation |
