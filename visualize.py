import requests
import matplotlib.pyplot as plt
from datetime import datetime

API_URL = "http://127.0.0.1:8000/sensor-data"
SENSOR_ID = "sensor-002"

# Fetch data
params = {"sensor_id": SENSOR_ID, "limit": 100}
response = requests.get(API_URL, params=params)
data = response.json()["result"]

# Sort data by timestamp
data = sorted(data, key=lambda x: x["timestamp"])

timestamps = []
values = []
anomalies = []
scores = []

for r in data:
    timestamps.append(datetime.fromisoformat(r["timestamp"]))
    values.append(r["value"])
    anomalies.append(r["anomaly"])
    scores.append(r.get("score", 0))

# Create plot with two y-axes
fig, ax1 = plt.subplots()

# Plot sensor values
ax1.plot(timestamps, values, label="Value")
ax1.set_xlabel("Time")
ax1.set_ylabel("Sensor Value")

# Highlight anomalies
for i in range(len(values)):
    if anomalies[i]:
        ax1.scatter(timestamps[i], values[i])

# Secondary axis for score
ax2 = ax1.twinx()
ax2.plot(timestamps, scores, label="Score")
ax2.set_ylabel("Anomaly Score")

# Title and formatting
plt.title(f"Sensor Data - {SENSOR_ID}")
plt.xticks(rotation=45)
plt.tight_layout()

plt.show()