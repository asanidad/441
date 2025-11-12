"""
Lab 8 — Stepper Motor Control (driver)

- Uses the Stepper class above with a shared Shifter.
- Creates two *separate* locks so the motors operate simultaneously even
  if rotate()/goAngle() are called one after the other.

Sequence required by the prompt:
    m1.zero(); m2.zero()
    m1.goAngle(90)
    m1.goAngle(-45)
    m2.goAngle(-90)
    m2.goAngle(45)
    m1.goAngle(-135)
    m1.goAngle(135)
    m1.goAngle(0)
"""

import time
import multiprocessing
from stepper_class_shiftregister_multiprocessing import Stepper, Shifter

def main():
    # Shifter pins: SER=16, LATCH=20, CLOCK=21 (keep your wiring the same)
    s = Shifter(16, 21, 20)   # SER=16, LATCH=20, CLOCK=21  (positional args)

    # IMPORTANT: give each motor its *own* lock to enable simultaneous moves.
    lock1 = multiprocessing.Lock()
    lock2 = multiprocessing.Lock()

    m1 = Stepper(s, lock1)
    m2 = Stepper(s, lock2)

    # 1) zero
    m1.zero()
    m2.zero()
    time.sleep(0.2)

    # 2) commands (each call spawns a process; motors run together if their moves overlap)
    m1.goAngle(90)
    m1.goAngle(-45)

    m2.goAngle(-90)
    m2.goAngle(45)

    m1.goAngle(-135)
    m1.goAngle(135)
    m1.goAngle(0)

    # keep main alive so child processes can finish
    print("Running demo…  Press CTRL+C to stop.")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting.")

if __name__ == "__main__":
    main()
