# AI Predictive Maintenance System — Technical Architecture Blueprint

> **Target Asset:** Industrial End-Suction Centrifugal Irrigation Pump (Standard: Grundfos NB / Kirloskar DB Series)
> **Asset Classification:** Class II Industrial Machinery under ISO 10816-3 (Medium-sized machines 15 kW to 75 kW on rigid foundations)
> **Application:** Continuous Irrigation & Water Distribution Station
> **Version:** 2.0 — Production-Ready AI & RAG Specification
> **Audience:** AI Team, Backend Team, MLOps, Domain Experts

---

## 1. System High-Level Architecture

The AgriPulse end-to-end architecture continuously ingests operational telemetry from centrifugal irrigation pumps, assesses asset health using a causal machine learning engine, correlates statistical anomalies with maintenance engineering standards, and produces actionable work orders via an LLM/RAG assistant. All subsystems communicate via a **Unified API Gateway (Port 8000)** and an **Asynchronous Redis Event Bus**, providing sub-second real-time responsiveness to the React 18 frontend.

```mermaid
flowchart TD
    subgraph Edge ["1. Edge & IoT Test Bench"]
        HW["ESP32 Microcontroller\n8 Sensors (ADXL345, SCT-013, DS18B20, G1/4)\n1-min ISO-8601 Packets"]
    end

    subgraph Gateway ["2. Unified Ingress & API Gateway (Port 8000)"]
        GW["FastAPI Central Ingress Gateway\nReverse Proxy / APIRouter (Port 8000)\n- REST API: /api/v1/*\n- WebSocket: /ws/telemetry & /ws/alerts"]
    end

    subgraph DataPlane ["3. Data & Messaging Backbone"]
        REDIS[("Redis 7 In-Memory Bus\nPub/Sub & Fast State Cache\n- telemetry:raw\n- telemetry:scored\n- alerts:trigger")]
        TSDB[("PostgreSQL 16 + TimescaleDB\nHypertables: sensor_telemetry\nTables: weibull_predictions, alerts, work_orders")]
    end

    subgraph AIServices ["4. Intelligent Processing Services (Internal Mesh)"]
        ML["Causal ML & Prognostics Engine\n- ExtraTrees Classifier (Core 7)\n- Dynamic Z-Score Attribution\n- Weibull RUL Hazard Estimator"]
        RAG["RAG Diagnostic Assistant\n- ChromaDB: agripulse_knowledge\n- ISO 10816-3, ANSI/HI 9.6, Grundfos NB O&M\n- Auto Work Order & LOTO Synthesizer"]
        YOLO["Field Vision Engine (YOLOv8)\n- Foliar Pathology Scan\n- Agro-Hydraulic Stress Correlation"]
    end

    subgraph Client ["5. Presentation & Control Layer"]
        UI["React 18 / Vite Web Dashboard\n- Fleet Overview & Pump Digital Twin\n- Real-Time Gauges & Strip Charts\n- Weibull Hazard Curves & WO Management"]
    end

    %% Communication Flows
    HW -->|"1. HTTPS POST /api/v1/telemetry/ingest"| GW
    GW -->|"2. Write Raw Hypertable"| TSDB
    GW -->|"3. Publish 'telemetry:raw'"| REDIS

    REDIS -->|"4. Consume Raw Packet"| ML
    ML -->|"5. Store RUL & Scores"| TSDB
    ML -->|"6. Publish 'telemetry:scored'"| REDIS

    REDIS -->|"7. On Score >= Warning/Critical"| RAG
    RAG -->|"8. Draft Work Order & LOTO"| TSDB

    YOLO -.->|"Agro-Hydraulic Query"| GW
    GW -.->|"Telemetry Snapshot"| YOLO

    REDIS -->|"9. Live Broadcast"| GW
    GW -->|"10. WebSocket Push (Sub-second)"| UI
    UI -->|"11. REST API Commands (/api/v1/*)"| GW
```

---

## 2. Target Machine Mechanical & Electrical Mapping

The AI architecture monitors the exact critical points of a standard **End-Suction Centrifugal Irrigation Pump**:

```
       [ELECTRIC MOTOR]               [COUPLING]              [PUMP VOLUTE]
   +-----------------------+              ||              +-------------------+
   |                       |              ||              |     Impeller      |
   | [sensor_05 / 11]      |         [sensor_13]          |                   |====> Discharge Line
   | Motor Phase Currents  |      Coupling Vibration      |                   |      
   |                       |                              | [sensor_28]       |
   | [sensor_00]           |                              | Discharge Flow    |
   | Motor DE Bearing Vib  |                              +-------------------+
   |                       |                                        |
   | [sensor_40]           |                                        | Suction Line
   | Motor DE Bearing Temp |                                        v
   +-----------------------+
```

### The Core 7 Sensor Group:

| Sensor ID | Monitored Point on Pump Asset | Physical Phenomenon & Failure Modes Monitored | Engineering Standard Reference |
| :--- | :--- | :--- | :--- |
| **`sensor_00`** | Motor Drive-End (DE) Bearing | Radial vibration severity, rotor unbalance, ball/race defects | ISO 10816-3 Class II (Zone A to D) |
| **`sensor_04`** | Motor Output Shaft | Rotational speed (RPM), motor slip, torque pulsation | NEMA MG 1 Motor Standards |
| **`sensor_05`** | Motor Stator Feed (Phase A) | Current draw (Amperes), winding load, impeller clogging | IEC 60034-1 Electric Ratings |
| **`sensor_11`** | Motor Stator Feed (Phase B) | Phase balance, voltage sag, single-phasing detection | IEEE 519 / NEMA MG 1 |
| **`sensor_13`** | Mechanical Flexible Coupling | Axial & horizontal vibration, angular/parallel misalignment | ISO 10816-3 Coupling Thresholds |
| **`sensor_28`** | Pump Volute / Discharge Flange | Flow rate delivery proxy, hydraulic cavitation, air ingestion | ANSI/HI 9.6.1 Cavitation Margin |
| **`sensor_40`** | DE Bearing External Housing | Lubricant breakdown, overheating, frictional degradation | SKF Bearing Operating Temp Limit (<80°C) |

---

## 3. Machine Learning Inference Engine Specification

### 3.1 Model Algorithm & Training Regime
* **Model Class:** `ExtraTreesClassifier` (Extremely Randomized Ensembles).
* **Sensor Set:** Core 7 Sensors (`sensor_00`, `04`, `05`, `11`, `13`, `28`, `40`).
* **Validation Methodology:** Strict 3-Way Temporal Split:
  * **Train Set:** Fits decision trees exclusively on historical baseline operations.
  * **Independent Calibration Set:** Extracts operational percentiles without label leakage.
  * **Blind Test Set:** Completely untouched out-of-sample failure events.

### 3.2 Dual-Tier Operational Thresholds
* **WARNING Level (`0.2713`):** 95th percentile of normal operational variance. Flags initial component degradation (e.g., initial coupling jitter or minor cavitation).
* **CRITICAL Level (`0.3169`):** 98.5th percentile. Signals imminent functional breakdown requiring load reduction or controlled shutdown.

### 3.3 Root-Cause Attribution via Dynamic Z-Deviation
The engine computes a localized Z-score relative to each sensor's 60-minute rolling baseline:
$$\mathcal{Z}_s(t) = \frac{|x_s(t) - \mu_{s, 60m}|}{\sigma_{s, 60m} + \epsilon}$$
The sensor exhibiting the highest relative deviation $\max_s(\mathcal{Z}_s)$ is flagged as the **Attributed Sensor**. This pinpoints whether the failure is electrical (motor currents), mechanical (bearing/coupling vibration), or hydraulic (flow/pressure).

---

## 4. Domain-Specific RAG Knowledge Base Architecture

The RAG Assistant does not rely on generic LLM knowledge. It queries a domain-specific vector database populated with industrial standards and manuals for **End-Suction Centrifugal Pumps**:

```
knowledge_base/
├── standards/
│   ├── iso_10816_3_vibration_severity_guidelines.md
│   ├── ansi_hi_9_6_centrifugal_pump_operation.md
│   └── iec_60034_motor_thermal_limits.md
├── manuals/
│   ├── centrifugal_irrigation_pump_om_manual.md
│   └── flexible_coupling_alignment_and_maintenance.md
└── fmea/
    ├── fmea_centrifugal_pump_bearings.md
    ├── fmea_hydraulic_cavitation_and_clogging.md
    └── fmea_coupling_misalignment_and_wear.md
```

### 4.1 FMEA Attribution Mapping Matrix

When the AI engine flags an alert, the RAG pipeline automatically retrieves the precise troubleshooting protocol:

| Attributed Sensor | Primary Failure Mode Identified | Specific Engineering Actions (from RAG Manuals) | Spare Parts & Tools |
| :--- | :--- | :--- | :--- |
| **`sensor_00`** | Bearing Race Flaking / Unbalance | 1. Check casing vibration velocity (RMS mm/s).<br>2. Inspect lubrication interval and grease quality.<br>3. Inspect DE bearing clearance. | Deep groove ball bearing (SKF 6308 or equivalent), Dial indicator, Grease gun (Lithium EP2). |
| **`sensor_13`** | Flexible Coupling Misalignment | 1. Measure radial and axial runout across coupling hubs.<br>2. Check for deteriorated elastomeric spider insert.<br>3. Verify motor base bolt torques. | Flexible spider insert, Stainless alignment shims (0.05–1.0 mm), Laser alignment tool. |
| **`sensor_05` / `sensor_11`** | Electrical Overload / Clogged Impeller | 1. Inspect suction strainer for weeds/sediment blockage.<br>2. Verify 3-phase resistance balance across stator.<br>3. Check for mechanical binding by hand-turning shaft. | Suction gasket set, Megohmmeter (500V Insulation tester), Multimeter clamp. |
| **`sensor_28`** | Hydraulic Cavitation / Recirculation | 1. Measure Net Positive Suction Head Available ($NPSH_A$).<br>2. Inspect suction line for air leaks or throttled foot valve.<br>3. Check discharge valve position. | Vacuum gauge, Replacement foot valve flapper, Pipe sealant. |
| **`sensor_40`** | Lubrication Starvation / Overheating | 1. Immediate bearing surface temperature probe check.<br>2. Verify bearing housing is not over-greased or dry.<br>3. Inspect shaft seal leakage spraying into bearing cavity. | High-temp synthetic grease, Replacement mechanical seal cartridge. |

---

## 5. Automated AI Work Order Generation

When status reaches `WARNING` or `CRITICAL`, the system triggers an asynchronous prompt execution:

### Prompt Payload Structure
```json
{
  "pump_id": "PUMP_IRRIGATION_001",
  "status": "CRITICAL",
  "health_index_pct": 43.0,
  "risk_score": 0.342,
  "attributed_sensor": "sensor_13",
  "sensor_telemetry_snapshot": {
    "sensor_00_vib_de": 2.85,
    "sensor_13_vib_coupling": 5.42,
    "sensor_05_current_a": 16.2,
    "sensor_40_temp_c": 54.1
  },
  "retrieved_context": "[ANSI/HI 9.6.5 Coupling Misalignment Standards & Grundfos NB Maintenance Chapter 6]"
}
```

### Expected Output Work Order Schema (Returned to Dashboard)
```json
{
  "work_order_id": "WO-IRR-20180708-01",
  "pump_model": "Grundfos NB 65-200 End-Suction Centrifugal",
  "urgency": "CRITICAL — Action Required Within 30 Minutes",
  "failure_diagnosis": "Severe Angular Misalignment / Degradation of Coupling Element",
  "lead_time_buffer": "30 minutes remaining before functional trip",
  "standards_reference": "ISO 10816-3 Zone C/D Boundary Exceeded",
  "immediate_mitigation": [
    "Throttling pump discharge slightly to reduce axial thrust loads.",
    "Alert on-duty mechanical technician for site inspection."
  ],
  "inspection_checklist": [
    "1. Power lock-out / tag-out (LOTO) motor starter.",
    "2. Remove coupling guard and inspect elastomeric element for shredding or heat cracking.",
    "3. Place dial indicator on pump shaft; rotate 360° to assess angular runout (< 0.05 mm required).",
    "4. Retorque baseplate anchor bolts to 85 Nm."
  ],
  "required_parts": [
    "Flexible coupling spider insert (Size 110)",
    "Shim pack (0.1 mm, 0.2 mm, 0.5 mm)"
  ]
}
```

---

## 6. Unified Architecture & Subsystem Communication Contracts

Rather than exposing multiple fragmented ports to clients, AgriPulse implements a **Single-Ingress API Gateway (Port 8000)** paired with an **Internal Redis 7 Event Bus**. This guarantees that the React 18 frontend, the ESP32 IoT edge gateway, and external clients interface with a single secure, authenticated surface while internal AI engines process telemetry asynchronously.

### 6.1 Subsystem Communication Matrix

| Source Subsystem | Destination Subsystem | Protocol / Channel | Payload / Data Contract | Latency Target |
| :--- | :--- | :--- | :--- | :--- |
| **ESP32 Edge Rig** | **Ingress Gateway** | `HTTPS POST /api/v1/telemetry/ingest` (or MQTT `agripulse/pump/{id}/telemetry`) | JSON packet with Core 7 sensor metrics + timestamp | $< 200\text{ ms}$ |
| **Ingress Gateway** | **TimescaleDB** | Async SQL (`INSERT INTO sensor_telemetry`) | Raw telemetry record in hypertable | $< 25\text{ ms}$ |
| **Ingress Gateway** | **Redis Event Bus** | `PUBLISH telemetry:raw` | `{"pumpId": str, "timestamp": str, "sensors": dict}` | $< 5\text{ ms}$ |
| **Redis Event Bus** | **Causal ML Engine** | Redis Pub/Sub Subscription | Consumes `telemetry:raw`, pushes into 65-sample FIFO | Immediate |
| **Causal ML Engine** | **TimescaleDB** | Async SQL (`INSERT INTO weibull_predictions`) | `healthIndex`, `riskScore`, `attributedSensor`, `rulHours` | $< 50\text{ ms}$ |
| **Causal ML Engine** | **Redis Event Bus** | `PUBLISH telemetry:scored` | Scored telemetry packet with Weibull & Z-deviations | $< 5\text{ ms}$ |
| **Causal ML Engine** | **Redis Event Bus** | `PUBLISH alerts:trigger` (if score $\ge$ Warning/Critical) | Alert trigger event with ISO 10816-3 severity level | Immediate |
| **Redis Event Bus** | **RAG Assistant** | Redis Pub/Sub Subscription | Consumes `alerts:trigger`, retrieves ChromaDB context | $< 800\text{ ms}$ |
| **RAG Assistant** | **PostgreSQL** | Async SQL (`INSERT INTO work_orders`, `loto_checklists`) | Auto-drafted maintenance work order + LOTO | $< 100\text{ ms}$ |
| **Redis Event Bus** | **WebSocket Broadcaster** | Internal Async Loop | Relays `telemetry:scored` and `alerts:trigger` to `/ws` | $< 15\text{ ms}$ |
| **WebSocket Broadcaster** | **React 18 Frontend** | `WSS /ws/telemetry` & `WSS /ws/alerts` | Real-time telemetry frames and critical banner events | Sub-second |
| **Field Vision (YOLOv8)** | **Ingress Gateway** | Internal Service Call (`GET /api/v1/telemetry/snapshot/{id}`) | Correlates crop stress with pump discharge flow & pressure | $< 150\text{ ms}$ |

---

### 6.2 Redis Pub/Sub Event Schemas

#### Channel: `telemetry:raw`
Published immediately after Ingress Gateway validation:
```json
{
  "eventId": "evt-raw-1029384",
  "pumpId": "PUMP-001",
  "timestamp": "2026-10-25T01:00:00Z",
  "readings": {
    "sensor_00": 2.14,
    "sensor_04": 1780.0,
    "sensor_05": 14.8,
    "sensor_11": 14.7,
    "sensor_13": 2.89,
    "sensor_28": 182.4,
    "sensor_40": 48.2,
    "sensor_48": 4.12
  }
}
```

#### Channel: `telemetry:scored`
Published by the Causal ML & Prognostics engine:
```json
{
  "eventId": "evt-sc-9847120",
  "pumpId": "PUMP-001",
  "timestamp": "2026-10-25T01:00:01Z",
  "anomalyScore": 0.2840,
  "healthIndex": 71.6,
  "status": "WARNING",
  "attributedSensor": "sensor_13",
  "attributedPhenomenon": "Coupling Misalignment",
  "weibull": {
    "rulHours": 412.5,
    "failureProbability": 0.38,
    "shapeBeta": 2.15,
    "scaleEta": 1250.0
  },
  "zScores": {
    "sensor_00": 0.84,
    "sensor_13": 3.42,
    "sensor_05": 0.31,
    "sensor_40": 1.15
  }
}
```

#### Channel: `alerts:trigger`
Published when `anomalyScore >= 0.2713` or ISO 10816-3 threshold is breached:
```json
{
  "alertId": "alt-88291",
  "pumpId": "PUMP-001",
  "timestamp": "2026-10-25T01:00:01Z",
  "severity": "CRITICAL",
  "isoZone": "Zone D — Unacceptable",
  "metric": "Coupling Vibration",
  "currentValue": 7.82,
  "threshold": 7.10,
  "unit": "mm/s RMS",
  "attributedSensor": "sensor_13"
}
```

---

### 6.3 Unified API Gateway Endpoint Map (Port 8000)

| Route Prefix | Underlying Engine / Service | Description |
| :--- | :--- | :--- |
| **`/api/v1/auth/*`** | Security Service | JWT token generation, refresh, engineer profile, RBAC |
| **`/api/v1/pumps/*`** | Asset Digital Twin | Pump specifications, BEP curves, health status, nameplate data |
| **`/api/v1/telemetry/*`** | Ingestion & TimescaleDB | Ingest ESP32 telemetry, query historical trends, fetch live snapshot |
| **`/api/v1/predictions/*`** | ML & Prognostics | Weibull RUL curves, failure probability, SHAP/Z-score attributions |
| **`/api/v1/alerts/*`** | Incident Management | Active alert list, acknowledge, escalate, resolution log |
| **`/api/v1/work-orders/*`** | Maintenance Planner | Auto-generated & manual work orders, LOTO safety checklists |
| **`/api/v1/assistant/*`** | RAG Diagnostic Service | Interactive technician chat, automated FMEA synthesis |
| **`/api/v1/vision/*`** | YOLOv8 Engine | Foliar pathology scans, Agro-Hydraulic stress cross-correlation |
| **`/api/v1/dashboard/*`** | Fleet Aggregator | High-level fleet KPIs, energy efficiency, MTBF, irrigation sectors |
| **`/ws/telemetry`** | WebSocket Gateway | Real-time push of `telemetry:scored` packets to frontend |
| **`/ws/alerts`** | WebSocket Gateway | Sub-second push of critical alarm banners and emergency stop signals |
