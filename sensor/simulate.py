import time
import math 
import random 
import argparse
from datetime import datetime, timezone


# This returns current UTC time in ISO format 
def now_iso():
    return datetime.now(timezone.utc).isoformat()
# To generate a realistic sensor value
def generate_value(t):
    base = 25 # the baseline temp (constant center value)
    amplitude = 2 # how high and low the wave will oscillate
    period = 60 # one full sine wave cycle takes 60 seconds
    noise = random.gauss(0, 0.2) # small random variation (mean = 0, std = 0.2)

    # this creates smooth oscillation like real temp
    wave = amplitude * math.sin(2 * math.pi * t / period)

    # final sensor value:
    # base level + smooth oscillation + small random noise
    return base + wave + noise

# We need controlled attack modes to test detection later
# each aatack changes the data in a predictable way
def apply_attack(mode, value, t):
    # Attack 1: injection 
    # Reason: Simulates sudden malicious spikes (common use in naive sensor spoofing)
    if mode == "inject":
        # Every ~15 secs, add a big spike
        # int(t) turns elapsed time into whole seconds so the trigger is stable
        if int(t) % 15 == 0:
            return value + 15
        return value
    
    # Attack 2: drift
    # Reason: to simulate stealthy manipulation that looks "normal" at first
    # this is harder to catch with simple thresholds
    if mode == "drift":
        return value + (0.02 * t)
    
    # no attack 
    return value 



def main():
    # Need argparse to change behavior without editing the code
    # this is cleaner for testing, automation, running multiple terminals, and later CI
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--attack",
        choices=["none", "inject", "drift"],
        default="none",
        help="Select attack mode for the stream"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Seconds between readings"
    )
    args = parser.parse_args()

    start = time.time() # store the starting time once 

    while True:  # infinite loop, simulates real sensor streaming 
        t = time.time() - start # this tells how many seconds have passed

        value = generate_value(t) # computes sensor reading 
        value = apply_attack(args.attack, value, t) # optional tampering

        payload = {
        "timestamp": now_iso(),
        "value": round(value, 3),
        "attack": args.attack
        }


        print(payload) # prints the sensor reading to the terminal 
        time.sleep(args.interval) # controls the sampling rate


# only runs main() if this file is executed directly 
# not if it is imported as a module
if __name__ == "__main__":
    main()