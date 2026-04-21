from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# to create FastAPI app instance
app = FastAPI()

# In memory storage
READINGS = []

# Stores last reading per sensor_id 
LAST_BY_SENSOR = {}

# Data model for incoming sensor data 
class SensorReading(BaseModel):
    timestamp: datetime
    value: float 
    attack: str 
    sensor_id: str


# global state additions for detection logic
HISTORY_BY_SENSOR = {}
WINDOW_SIZE = 5
DRIFT_THRESHOLD = 5.0
RATE_THRESHOLD = 0.9
MIN_VALUE = 10.0
MAX_VALUE = 40.0
MAX_PHYSICAL_RATE = 2.0
ANOMALY_SCORE_BY_SENSOR = {}
SENSOR_STATE = {}
SUSPICIOUS_THRESHOLD = 3
COMPROMISED_THRESHOLD = 6
DECAY_AMOUNT = 1.0
DETECTION_STATS = {}
BASELINE_WINDOW = 60
BASELINE_THRESHOLD = 5.0
BASELINE_HISTORY = {}

# Health check endpoint
@app.post("/sensor-data")
def ingest(reading: SensorReading):

    anomaly = False
    spike_triggered = False
    baseline_triggered = False
    drift_triggered = False
    rate_triggered = False
    physics_triggered = False

    previous = LAST_BY_SENSOR.get(reading.sensor_id)

    # Layer 1: Instant spike detection
    if previous:
        delta = abs(reading.value - previous["value"])
        if delta > 3.0:
            anomaly = True
            spike_triggered = True

   # Layer 4: Hard physical bounds
    if reading.value < MIN_VALUE or reading.value > MAX_VALUE:
        anomaly = True
        physics_triggered = True
    

    # Initialize history if needed
    if reading.sensor_id not in HISTORY_BY_SENSOR:
        HISTORY_BY_SENSOR[reading.sensor_id] = []

    history = HISTORY_BY_SENSOR[reading.sensor_id]

    # Append structured history entry
    history.append({
        "value": reading.value,
        "timestamp": reading.timestamp
    })

    # --- Baseline history (detection)---
    if reading.sensor_id not in BASELINE_HISTORY:
        BASELINE_HISTORY[reading.sensor_id] = []

    baseline = BASELINE_HISTORY[reading.sensor_id]

    baseline_ready = len(baseline) >= BASELINE_WINDOW

    # Only perform baseline detection if we have enough data
    if len(baseline) == BASELINE_WINDOW:

        mean = sum(baseline) / len(baseline)
        variance = sum((x - mean) ** 2 for x in baseline) / len(baseline)
        stddev = variance ** 0.5

        if stddev > 0:
            tolerance = max(BASELINE_THRESHOLD * stddev, 1.5)  # Ensure minimum tolerance
            
            if abs(reading.value - mean) > tolerance:
                anomaly = True
                baseline_triggered = True
        

    # --- Baseline update (allow training phase) ---
    if len(baseline) < BASELINE_WINDOW:
    # Initial training phase (only clean data)
        if reading.attack == "none":
            baseline.append(reading.value)
    else:
        # After baseline is trained, this is to protect it 
       if reading.attack == "none" and not anomaly:
            baseline.append(reading.value)
            if len(baseline) > BASELINE_WINDOW:
                 baseline.pop(0)


    # Keep window fixed size
    if len(history) > WINDOW_SIZE:
        history.pop(0)

    # Window-based logic (Layers 2, 3, 5)
    if len(history) == WINDOW_SIZE:

        value_delta = history[-1]["value"] - history[0]["value"]

        time_delta = (
            history[-1]["timestamp"] - history[0]["timestamp"]
        ).total_seconds()

        if time_delta > 0:

            drift = abs(value_delta)
            rate = abs(value_delta / time_delta)

            # Layer 2: Drift threshold
            if drift > DRIFT_THRESHOLD:
                anomaly = True
                drift_triggered = True

            # Layer 3: Rate-of-change threshold
            if rate > RATE_THRESHOLD:
                anomaly = True
                rate_triggered = True

            # Layer 5: Physics maximum rate
            if rate > MAX_PHYSICAL_RATE:
                anomaly = True
                physics_triggered = True

    # --- Sensor level scoring with decay ---
    if reading.sensor_id not in ANOMALY_SCORE_BY_SENSOR:
        ANOMALY_SCORE_BY_SENSOR[reading.sensor_id] = 0
    
    score = ANOMALY_SCORE_BY_SENSOR[reading.sensor_id]

    # --- initialize detection stats if needed ---
    if reading.sensor_id not in DETECTION_STATS:
        DETECTION_STATS[reading.sensor_id] = {
            "total_readings": 0,
            "anomaly_count": 0,
            "suspicious_transitions": 0,
            "compromised_transitions": 0
        }

    stats = DETECTION_STATS[reading.sensor_id]

    # Increment total readings
    stats["total_readings"] += 1

    # Increment anomaly counter
    if anomaly:
        stats["anomaly_count"] += 1


    if anomaly:
        score += 1
    else:
        score -= DECAY_AMOUNT

    # Prevent negative scores
    if score < 0:
        score = 0
    
    ANOMALY_SCORE_BY_SENSOR[reading.sensor_id] = score

    # Determine sensor state with hysteresis
    previous_state = SENSOR_STATE.get(reading.sensor_id, "NORMAL")

    if score >= COMPROMISED_THRESHOLD:
        state = "COMPROMISED"
    elif score >= SUSPICIOUS_THRESHOLD:
        state = "SUSPICIOUS"
    else:
        # recovery logic 
        if previous_state == "COMPROMISED" and score > (COMPROMISED_THRESHOLD - 1):
            state = "SUSPICIOUS"
        elif previous_state == "SUSPICIOUS" and score > 0:
            state = "SUSPICIOUS"
        else:
            state = "NORMAL"

    
    previous_state = SENSOR_STATE.get(reading.sensor_id, "NORMAL")

    # track state transitions
    if previous_state != state:
        if state == "SUSPICIOUS":
            stats["suspicious_transitions"] += 1
        elif state == "COMPROMISED":
            stats["compromised_transitions"] += 1

    SENSOR_STATE[reading.sensor_id] = state



    # Convert model to dictionary
    data = reading.model_dump()
    data["anomaly"] = anomaly
    data["score"] = score

    data["reason" ] = {
        "spike": spike_triggered,
        "baseline": baseline_triggered,
        "drift": drift_triggered,
        "rate": rate_triggered,
        "physics": physics_triggered
    }

    data["baseline_ready"] = baseline_ready

    READINGS.append(data)
    LAST_BY_SENSOR[reading.sensor_id] = data

    return {
        "stored": True,
        "sensor_id": reading.sensor_id,
        "total_readings": len(READINGS)
    }

# get latest reading per sensor
@app.get("/sensor-data/latest")
def latest(sensor_id: Optional[str] = None):
    
    if sensor_id:
        latest = LAST_BY_SENSOR.get(sensor_id)

        return {
            "sensor_id": sensor_id,
            "state": SENSOR_STATE.get(sensor_id, "NORMAL"),
            "score": ANOMALY_SCORE_BY_SENSOR.get(sensor_id, 0),
            "baseline_ready": latest.get("baseline_ready") if latest else False,
            "latest_reading": latest
        }
    
    return {
        "all_latest": LAST_BY_SENSOR
    }

# query historical readings
@app.get("/sensor-data")
def get_readings(sensor_id: Optional[str] = None, limit: int = 50):

    if sensor_id:
        filtered = [r for r in READINGS if r["sensor_id"] == sensor_id]
    else:
        filtered = READINGS

    return {
        "counts": len(filtered),
        "result": filtered[-limit:]
    }
    
# Stats endpoint 
@app.get("/sensor-data/stats")
def get_stats(sensor_id: Optional[str] = None):

    if sensor_id:
        return {
            "sensor_id": sensor_id,
            "stats": DETECTION_STATS.get(sensor_id, {})
        }
        
    return {
        "all_stats": DETECTION_STATS
    }

# System status endpoint
@app.get("/system/status")
def system_status():
    counts = {"NORMAL": 0, "SUSPICIOUS": 0, "COMPROMISED": 0}

    for state in SENSOR_STATE.values():
        counts[state] += 1

    return {
        "total_sensors": len(SENSOR_STATE),
        "state_counts": counts,
        "sensors": [
            {
                "sensor_id": sid,
                "state": SENSOR_STATE[sid],
                "score": ANOMALY_SCORE_BY_SENSOR.get(sid, 0)
            }
            for sid in SENSOR_STATE
        ]
    }