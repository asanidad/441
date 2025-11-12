# lab8.py
# ENME441 – Lab 8 (Simultaneous Stepper Motion - Slowed Down)

from stepper_class_shiftregister_multiprocessing import Shifter, Stepper, SyncController
import RPi.GPIO as GPIO
import time

# --- 74HC595 pin connections (BCM numbers) ---
SER_PIN   = 16   # DS
LATCH_PIN = 20   # ST_CP
CLOCK_PIN = 21   # SH_CP

def move_together(ctrl, m1, a1, m2, a2, dwell=0.5):
    """
    Move both motors simultaneously to new absolute targets.
    """
    print(f"Moving: M1→{a1}°, M2→{a2}°")
    m1.set_target(a1)
    m2.set_target(a2)
    ctrl.run_until_all_reached([m1, m2])
    time.sleep(dwell)

def main():
    s = Shifter(serialPin=SER_PIN, latchPin=LATCH_PIN, clockPin=CLOCK_PIN)
    ctrl = SyncController(s)

    # Two steppers, both driven by one 74HC595
    m1 = Stepper(nibble='low',  steps_per_rev=200, step_delay=0.01)   # slower = visible motion
    m2 = Stepper(nibble='high', steps_per_rev=200, step_delay=0.01)

    # Reset and start
    m1.zero()
    m2.zero()
    ctrl.run_until_all_reached([m1, m2])

    print("Running simultaneous motion demo... Press CTRL+C to stop.")
    try:
        # Both move at once for each pair of commands
        move_together(ctrl, m1, 90,  m2, -90)     # Opposite directions
        move_together(ctrl, m1, -45, m2, 45)      # Swap directions
        move_together(ctrl, m1, 135, m2, -135)    # Wider rotation
        move_together(ctrl, m1, 0,   m2, 0)       # Return home
        print("Done.")
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
