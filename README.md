# Physics-Aware Sensor Tamper Detection System

## Overview
This project simulates and detects compromised sensor data in real time. It combines physics-based constraints, statistical modeling, and stateful scoring to identify abnormal behavior and classify sensor risk levels.

The system ingests live sensor data, learns normal behavior, detects anomalies, and tracks each sensor’s state over time.

---

## Features

- Real-time sensor data ingestion using FastAPI
- Baseline learning from normal sensor behavior
- Multi-layer anomaly detection:
  - Instant spike detection
  - Baseline deviation detection
  - Drift detection
  - Rate-of-change detection
  - Physics-based bounds
- Sensor risk scoring with decay
- State transitions:
  - NORMAL → SUSPICIOUS → COMPROMISED
- Multi-sensor monitoring
- Visualization of sensor values and anomaly scores
- Simulated attack scenarios (inject and drift)

---

## System Architecture

- `api/main.py`  
  Backend API that ingests data, runs detection logic, and tracks sensor state

- `sensor/simulate.py`  
  Simulates sensor data and attack scenarios

- `visualize.py`  
  Plots sensor values, anomalies, and score over time

- `demo/demo.mp4`  
  Screen recording showing the system in action

---

## Detection Logic

The system uses multiple layers to detect anomalies:

- **Spike Detection**  
  Flags sudden jumps between consecutive readings

- **Baseline Deviation**  
  Compares current value against a learned baseline mean and standard deviation

- **Drift Detection**  
  Detects gradual shifts over a sliding window

- **Rate-of-Change**  
  Ensures changes stay within realistic limits

- **Physics Constraints**  
  Enforces min/max bounds and maximum physical rate

The baseline is trained only on clean data to prevent poisoning.

---

## Sensor Scoring and State

Each sensor maintains a score:

- Score increases when anomalies are detected
- Score decays when readings return to normal
- Score determines sensor state:

| Score Range | State        |
|------------|-------------|
| 0–2        | NORMAL       |
| 3–5        | SUSPICIOUS   |
| 6+         | COMPROMISED  |

---

## API Endpoints

### Ingest Data

POST /sensor-data


### Latest Sensor State

GET /sensor-data/latest?sensor_id=sensor-002


### Historical Data

GET /sensor-data?sensor_id=sensor-002


### System Status

GET /system/status


---

## Demo

The demo shows the full workflow:

1. System learns normal sensor behavior
2. A simulated attack injects abnormal values
3. Anomaly detection triggers
4. Score increases and state changes
5. System recovers when behavior returns to normal

Watch the demo here:

demo/demo.mp4


---

## How to Run

### 1. Start backend

python -m uvicorn api.main:app --reload --port 8000


### 2. Run normal sensor (baseline training)

python sensor/simulate.py --attack none --sensor-id sensor-002


### 3. Run attack simulation

python sensor/simulate.py --attack inject --sensor-id sensor-002


### 4. View system status

curl "http://127.0.0.1:8000/system/status
"


### 5. Visualize data

python visualize.py


---

## Key Takeaways

- Demonstrates real-time anomaly detection
- Shows how baseline modeling can be poisoned and protected
- Uses multiple detection layers instead of a single threshold
- Tracks system state over time, not just individual events

---

## Future Improvements

- Web dashboard for live monitoring
- Multi-sensor correlation detection
- Persistent database storage
- Alerting system for compromised sensors