# lab8.py
# ENME441 – Lab 8: Stepper Motor Control
# Runs the instructor's command sequence with both motors operating simultaneously.

from stepper_class_shiftregister_multiprocessing import Shifter, Stepper, SyncController
import RPi.GPIO as GPIO
import time

# ---- 74HC595 wiring (BCM) ----
SER_PIN   = 16   # DS
LATCH_PIN = 20   # ST_CP
CLOCK_PIN = 21   # SH_CP

STEPS_PER_REV = 2048   # 28BYJ-48 full-step (AB→BC→CD→DA) via ULN2003
STEP_DELAY    = 0.010  # 10 ms between steps (safe speed)

def run_until_reached(ctrl, m1, m2, dwell=0.4):
    """Drive both motors until both have reached their current targets."""
    ctrl.run_until_all_reached([m1, m2])
    if dwell > 0:
        time.sleep(dwell)

def main():
    # Shift register + controller
    s = Shifter(serialPin=SER_PIN, latchPin=LATCH_PIN, clockPin=CLOCK_PIN)
    ctrl = SyncController(s)

    # Two steppers on the same 74HC595 (Q0..Q3 = m1, Q4..Q7 = m2)
    m1 = Stepper(nibble='low',  steps_per_rev=STEPS_PER_REV, step_delay=STEP_DELAY)
    m2 = Stepper(nibble='high', steps_per_rev=STEPS_PER_REV, step_delay=STEP_DELAY)

    print("Zeroing both motors…")
    m1.zero()
    m2.zero()
    run_until_reached(ctrl, m1, m2)

    print("Running lab sequence with simultaneous operation… (CTRL+C to stop)")
    try:
        print("Calibrating one full turn on M1...")
        m1.set_target(360)                 # ask for 360 degrees on Motor 1
        m2.set_target(0)                   # keep Motor 2 still
        ctrl.run_until_all_reached([m1, m2])
        print("Done. Did M1 turn exactly 360°?")

        # The sequence from the prompt:
        # m1.zero(); m2.zero(); (already done above)
        # m1.goAngle(90)
        """
        m1.set_target(90)         # change ONLY m1 target
        # keep both in the scheduler so they step on the same cadence
        run_until_reached(ctrl, m1, m2)

        # m1.goAngle(-45)
        m1.set_target(-45)
        run_until_reached(ctrl, m1, m2)

        # m2.goAngle(-90)
        m2.set_target(-90)
        run_until_reached(ctrl, m1, m2)

        # m2.goAngle(45)
        m2.set_target(45)
        run_until_reached(ctrl, m1, m2)

        # m1.goAngle(-135)
        m1.set_target(-135)
        run_until_reached(ctrl, m1, m2)

        # m1.goAngle(135)
        m1.set_target(135)
        run_until_reached(ctrl, m1, m2)

        # m1.goAngle(0)
        m1.set_target(0)
        run_until_reached(ctrl, m1, m2)
        """

        print("Sequence complete.")
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
