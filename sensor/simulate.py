import time
import math
import random
import argparse
import requests  
from datetime import datetime, timezone
def now_iso():
    # Returns current UTC timestamp in ISO format
    return datetime.now(timezone.utc).isoformat()


def generate_value(t):
    # Baseline smooth physical signal
    base = 25
    amplitude = 2
    period = 60
    noise = random.gauss(0, 0.2)

    wave = amplitude * math.sin(2 * math.pi * t / period)
    return base + wave + noise


def apply_attack(mode, value, t):
    # Simulate malicious injection spike
    if mode == "inject":
        if int(t) % 15 == 0:
            return value + 15
        return value

    # Simulate slow stealth drift
    if mode == "drift":
        return value + (0.02 * t)

    return value



# Function to send data to backend

def post_reading(url, payload):
    """
    Sends JSON payload to FastAPI backend.
    Returns (success_boolean, response_or_error).
    """
    try:
        # Send POST request with JSON body
        r = requests.post(url, json=payload, timeout=3)

        #  Raise error if status code is not 200
        r.raise_for_status()

        return True, r.json()

    except requests.RequestException as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--attack", choices=["none", "inject", "drift"], default="none")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--sensor-id", default="sensor-001")

    
    # NEW: API URL argument
    
    parser.add_argument(
        "--api-url",
        default="http://127.0.0.1:8000/sensor-data"
    )

    args = parser.parse_args()

    start = time.time()

    while True:
        t = time.time() - start
        value = generate_value(t)
        value = apply_attack(args.attack, value, t)

        
        # Payload structured to match FastAPI model
       
        payload = {
            "timestamp": now_iso(),
            "value": round(value, 3),
            "attack": args.attack,
            "sensor_id": args.sensor_id,
        }

        
        # NEW: Send data to backend instead of just printing
        
        ok, result = post_reading(args.api_url, payload)

        if ok:
            print(f"POST ok | value={payload['value']} | attack={payload['attack']}")
        else:
            print(f"POST failed | {result}")

        time.sleep(args.interval)


if __name__ == "__main__":
    main()