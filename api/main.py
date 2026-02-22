from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="Physics Sensor Backend", version="0.1.0")

# In-memory storage for now (fast MVP)
READINGS: List[dict] = []


class SensorReading(BaseModel):
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    value: float = Field(..., description="Sensor value")
    attack: str = Field("none", description="Attack mode label for testing")
    sensor_id: str = Field("sensor-001", description="Sensor identifier")


@app.get("/health")
def health():
    return {"status": "ok", "count": len(READINGS)}


@app.post("/sensor-data")
def ingest(reading: SensorReading):
    # Basic sanity check: timestamp should be parseable
    # We store the original string, but parsing here helps catch malformed payloads early
    datetime.fromisoformat(reading.timestamp.replace("Z", "+00:00"))

    record = reading.model_dump()
    READINGS.append(record)

    return {
        "stored": True,
        "count": len(READINGS),
        "latest": record
    }


@app.get("/sensor-data/latest")
def latest():
    if not READINGS:
        return {"latest": None}
    return {"latest": READINGS[-1]}