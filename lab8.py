# lab8.py — ENME441 Lab 8: Stepper Motor Control (simultaneous, shortest-path goAngle)
#
# This script assumes the class definitions from:
#   stepper_class_shiftregister_multiprocessing.py
# which provide:
#   Shifter(serialPin, clockPin, latchPin)
#   Stepper(shifter, startBit)
#
# The two steppers share one 74HC595.  We map:
#   Motor m1 -> Q0..Q3  (startBit=0)
#   Motor m2 -> Q4..Q7  (startBit=4)
#
# Both motors are commanded concurrently using multiprocessing so that
# sequential API calls issued to each motor can execute “at the same time”
# per the lab requirement.

from multiprocessing import Process
import time

# Import the course-provided classes
from stepper_class_shiftregister_multiprocessing import Shifter, Stepper

import RPi.GPIO as GPIO  # only for final cleanup here


def motor_sequence(motor: Stepper, angles):
    """
    Run a sequence of goAngle() commands on a Stepper object.
    The Stepper class (in the provided module) blocks inside movement calls,
    so running this in a separate Process allows simultaneous motion.
    """
    # Zero first, per lab directions
    motor.zero()
    # Then visit each commanded absolute angle
    for a in angles:
        motor.goAngle(a)
        # Optional short dwell so both motors' prints don’t mash together
        time.sleep(0.05)


def main():
    # ---------------------------------------------------------------------
    # 1) Configure the shifter to match the lecture / provided file pinout
    # ---------------------------------------------------------------------
    # NOTE: Your earlier call s = Shifter(data=…, latch=…, clock=…) failed because
    # the constructor expects the names below:
    s = Shifter(serialPin=16, latchPin=20, clockPin=21)

    # ---------------------------------------------------------------------
    # 2) Create two independent Stepper instances (two motors on one shifter)
    # ---------------------------------------------------------------------
    # Lower nibble (Q0..Q3) for motor 1, upper nibble (Q4..Q7) for motor 2.
    m1 = Stepper(s, startBit=0)
    m2 = Stepper(s, startBit=4)

    # ---------------------------------------------------------------------
    # 3) Define each motor’s command sequence (absolute angles, degrees)
    #    matching the lab’s demonstration list
    # ---------------------------------------------------------------------
    # Lab demo list (as provided):
    # m1.zero()
    # m2.zero()
    #
    # m1.goAngle(90)
    # m1.goAngle(-45)
    #
    # m2.goAngle(-90)
    # m2.goAngle(45)
    #
    # m1.goAngle(-135)
    # m1.goAngle(135)
    # m1.goAngle(0)

    # We will execute the m1 and m2 sequences *concurrently*. That is,
    # each Process will run its list in order while the other motor is free
    # to move at the same time.
    m1_angles = [90, -45, -135, 135, 0]
    m2_angles = [-90, 45]

    # ---------------------------------------------------------------------
    # 4) Launch both motors in parallel
    # ---------------------------------------------------------------------
    p1 = Process(target=motor_sequence, args=(m1, m1_angles))
    p2 = Process(target=motor_sequence, args=(m2, m2_angles))

    print("Starting both motors concurrently…  (Ctrl+C to stop)")
    p1.start()
    p2.start()

    # Wait for both to complete
    p1.join()
    p2.join()

    print("Done. Both sequences completed.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Stopping…")
    finally:
        # Make sure GPIO is left in a clean state regardless of how we exit.
        # (The provided class should also be cleaning up on its own; this is a safety net.)
        try:
            GPIO.cleanup()
        except Exception:
            pass
