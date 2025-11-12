# lab8.py
# ENME441 – Lab 8 demo script (simultaneous version)

from stepper_class_shiftregister_multiprocessing import Shifter, Stepper, SyncController
import RPi.GPIO as GPIO

# 74HC595 pin mapping (BCM)
SER_PIN   = 16   # DS (SER)
LATCH_PIN = 20   # ST_CP
CLOCK_PIN = 21   # SH_CP

def move_together(ctrl: SyncController, m1: Stepper, a1: float, m2: Stepper, a2: float):
    """
    Queue new absolute targets for both motors and run them
    *simultaneously* to completion.
    """
    m1.set_target(a1)
    m2.set_target(a2)
    ctrl.run_until_all_reached([m1, m2])

def main():
    s = Shifter(serialPin=SER_PIN, latchPin=LATCH_PIN, clockPin=CLOCK_PIN)
    ctrl = SyncController(s)

    # Two motors on one 74HC595:
    m1 = Stepper(nibble='low',  steps_per_rev=200, step_delay=0.003)   # Motor 1 → Q0..Q3
    m2 = Stepper(nibble='high', steps_per_rev=200, step_delay=0.003)   # Motor 2 → Q4..Q7

    # Zero both
    m1.zero()
    m2.zero()
    ctrl.run_until_all_reached([m1, m2])

    print("Running demo…  Press CTRL+C to stop.")
    try:
        # ----- Lab prompt sequence -----
        # 1) m1.goAngle(90)
        move_together(ctrl, m1, 90,  m2, m2.angle.value)

        # 2) m1.goAngle(-45)
        move_together(ctrl, m1, -45, m2, m2.angle.value)

        # 3) m2.goAngle(-90)
        move_together(ctrl, m1, m1.angle.value, m2, -90)

        # 4) m2.goAngle(45)
        move_together(ctrl, m1, m1.angle.value, m2, 45)

        # 5) m1.goAngle(-135)
        move_together(ctrl, m1, -135, m2, m2.angle.value)

        # 6) m1.goAngle(135)
        move_together(ctrl, m1, 135,  m2, m2.angle.value)

        # 7) m1.goAngle(0)
        move_together(ctrl, m1, 0,    m2, m2.angle.value)

        print("Done.")
    except KeyboardInterrupt:
        print("\nExiting.")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
