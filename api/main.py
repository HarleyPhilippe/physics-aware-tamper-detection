from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# to create FastAPI app instance
app = FastAPI()

# In meomory storage
READINGS = []

# Stores last reading per sensor_id 
LAST_BY_SENSOR = {}

# Data model for incoming sensor data 
class SensorReading(BaseModel):
    timestamp: datetime
    value: float 
    attack: str 
    sensor_id: str


# Health check endpoint
@app.post("/sensor-data")
def ingest(reading: SensorReading):

    # convert model to dictionary 
    data = reading.model_dump()

    # store in global readings list 
    READINGS.append(data)

    # update last reading per sensor 
    LAST_BY_SENSOR[reading.sensor_id] = data

    return {
        "stored": True,
        "sensor_id": reading.sensor_id,
        "total_readings": len(READINGS)
    }

# get latest reading per sensor
@app.get("/sensor-data/latest")
def latest(sensor_id: Optional[str] = None):
    
    # if specific sensor requested 
    if sensor_id:
        return {
            "sensor_id": sensor_id,
            "latest_reading": LAST_BY_SENSOR.get(sensor_id)
        }
    
    # if no sensor specified, return all latest
    return {
        "all_latest": LAST_BY_SENSOR
    }

# query historical readings
@app.get("/sensor-data")
def get_readings(sensor_id: Optional[str] = None, limit: int = 50):

    # filter by sensor if provided 
    if sensor_id:
       filtered = [r for r in READINGS if r["Sensor_id"] == sensor_id]
    else:
        filtered = READINGS

        # return last N records
        return {
            "counts": len(filtered),
            "result": filtered[-limit:]
        }
