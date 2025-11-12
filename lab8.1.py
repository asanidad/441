# lab8.py — ENME441 Lab 8: Stepper Motor Control (simultaneous + slowed)
# Uses professor's shifter via shim_shifter (bit-reversal wrapper).

from shim_shifter import Shifter                    # wrapper around prof's shifter.py
from stepper_class_shiftregister_multiprocessing import Stepper, SyncController
import RPi.GPIO as GPIO
import time

# ---------- wiring (BCM) ----------
# Your wiring: DATA=16, LATCH=20, CLOCK=21
# Prof's Shifter ctor = (data, clock, latch) — note the order.
SER_PIN   = 16   # DS (data)
CLOCK_PIN = 21   # SH_CP (clock)
LATCH_PIN = 20   # ST_CP (latch)

# ---------- motion tuning ----------
STEPS_PER_REV = 2048   # 28BYJ-48 full-step via ULN2003; use 4096 if you switch to half-step
STEP_DELAY    = 0.012  # slower = more visible (10–15 ms is safe)

def run_until_reached(ctrl, m1, m2, dwell=0.4):
    ctrl.run_until_all_reached([m1, m2])
    if dwell > 0:
        time.sleep(dwell)

def main():
    s = Shifter(data=SER_PIN, clock=CLOCK_PIN, latch=LATCH_PIN)
    ctrl = SyncController(s)

    # Two steppers on one 74HC595: low nibble = M1 (Q0..Q3), high nibble = M2 (Q4..Q7)
    m1 = Stepper(nibble='low',  steps_per_rev=STEPS_PER_REV, step_delay=STEP_DELAY)
    m2 = Stepper(nibble='high', steps_per_rev=STEPS_PER_REV, step_delay=STEP_DELAY)

    print("Zeroing both...")
    m1.zero(); m2.zero()
    run_until_reached(ctrl, m1, m2)

    print("Running lab sequence with simultaneous timing...")
    try:
        # EXACT PROMPT SEQUENCE, keeping both motors in the scheduler each time
        # m1.zero(); m2.zero();  (already done)
        print("m1 -> 90");     m1.set_target( 90);  m2.set_target(m2.angle.value); run_until_reached(ctrl, m1, m2)
        print("m1 -> -45");    m1.set_target(-45);  m2.set_target(m2.angle.value); run_until_reached(ctrl, m1, m2)
        print("m2 -> -90");    m1.set_target(m1.angle.value); m2.set_target(-90);  run_until_reached(ctrl, m1, m2)
        print("m2 -> 45");     m1.set_target(m1.angle.value); m2.set_target( 45);  run_until_reached(ctrl, m1, m2)
        print("m1 -> -135");   m1.set_target(-135); m2.set_target(m2.angle.value); run_until_reached(ctrl, m1, m2)
        print("m1 -> 135");    m1.set_target( 135); m2.set_target(m2.angle.value); run_until_reached(ctrl, m1, m2)
        print("m1 -> 0");      m1.set_target(   0); m2.set_target(m2.angle.value); run_until_reached(ctrl, m1, m2)

        print("Done.")
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
