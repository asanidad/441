# stepper_class_shiftregister_multiprocessing.py
#
# Stepper class using a 74HC595 “Shifter” and multiprocessing so
# two (or more) motors can move *simultaneously* when you call
# rotate()/goAngle() on each, even if those calls happen back-to-back.

import time
import multiprocessing
from shifter import Shifter   # your Shifter class from the repo

class Stepper:
    """
    Supports operation of an arbitrary number of stepper motors using
    one or more shift registers.

    A class attribute (shifter_outputs) keeps track of all shift-register
    output values for all motors. This allows simultaneous operation of
    multiple motors: each step updates only the 4 bits that belong to
    this motor while preserving the other motors’ bits.
    """

    # ---- class attributes ----
    num_steppers      = 0             # count instances
    shifter_outputs   = 0             # 8/16/etc. bits across all motors
    seq = [0b0001, 0b0011, 0b0010, 0b0110, 0b0100, 0b1100, 0b1000, 0b1001]  # CCW half-step seq
    delay = 1200                      # us between steps
    steps_per_degree  = 4096 / 360.0  # BYJ48 gearbox, half-steps

    def __init__(self, shifter: Shifter, lock: multiprocessing.Lock):
        self.s  = shifter                          # shared shifter
        # IMPORTANT: angle is shared across processes so child updates persist
        self.angle = multiprocessing.Value('d', 0.0)   # degrees (double, shared)
        self.step_state = 0                       # position in seq [0..7]
        self.shifter_bit_start = 4 * Stepper.num_steppers  # 4 bits per motor
        self.lock = lock                          # use different locks for simultaneity

        Stepper.num_steppers += 1

    # ---- helpers ----
    def __sgn(self, x):  # signum
        if x == 0:
            return 0
        return int(abs(x) / x)

    def __step(self, dir_: int):
        """Take one half-step (+1 or -1) for THIS motor, preserving the others."""
        # advance our step state within [0..7]
        self.step_state = (self.step_state + dir_) % 8

        # build a mask for *our* 4 control bits
        mask_for_this_motor = 0b1111 << self.shifter_bit_start
        # put our 4-bit pattern into place
        pattern_bits = Stepper.seq[self.step_state] << self.shifter_bit_start

        # clear just our bits, then OR in our new pattern (preserve other motors)
        Stepper.shifter_outputs &= ~mask_for_this_motor
        Stepper.shifter_outputs |= pattern_bits

        # push to the 74HC595(s)
        self.s.shiftByte(Stepper.shifter_outputs)

        # update the shared angle
        with self.angle.get_lock():
            self.angle.value = (self.angle.value + dir_ / Stepper.steps_per_degree) % 360.0

    # ---- motion primitives ----
    def __rotate(self, delta_deg: float):
        """Blocking worker: move by a relative delta (degrees)."""
        # Only protect the *shifter write* so separate motors with separate locks can overlap.
        # If you pass each motor a different Lock, their movements are simultaneous.
        num_steps = int(Stepper.steps_per_degree * abs(delta_deg))
        dir_ = self.__sgn(delta_deg)

        for _ in range(num_steps):
            with self.lock:          # hold while emitting the single step
                self.__step(dir_)
            time.sleep(Stepper.delay / 1e6)

    def rotate(self, delta_deg: float):
        """Spawn a process to rotate by 'delta_deg' (relative move)."""
        p = multiprocessing.Process(target=self.__rotate, args=(delta_deg,))
        p.daemon = True
        p.start()
        return p  # caller may ignore or keep if they want to join()

    def goAngle(self, target_deg: float):
        """
        Move to an absolute *output-shaft* angle in degrees, following the
        shortest path (wrap at ±180). Non-blocking (spawns a process).
        """
        # normalize target to [0, 360)
        t = target_deg % 360.0
        with self.angle.get_lock():
            c = self.angle.value

        # shortest signed delta in (−180, 180]
        delta = ((t - c + 180.0) % 360.0) - 180.0
        return self.rotate(delta)

    def zero(self):
        """Set the current position as 0° (shared value)."""
        with self.angle.get_lock():
            self.angle.value = 0.0


# ---- example (optional quick test) ----
if __name__ == '__main__':
    # Pins from slides/repo example: SER=16, LATCH=20, CLOCK=21
    s = Shifter(data=16, latch=20, clock=21)

    # Two separate locks -> simultaneous motion
    lock1 = multiprocessing.Lock()
    lock2 = multiprocessing.Lock()

    m1 = Stepper(s, lock1)
    m2 = Stepper(s, lock2)

    m1.zero(); m2.zero()

    # demo: both run at the same time
    m1.rotate(180)
    m2.rotate(-180)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nend")
