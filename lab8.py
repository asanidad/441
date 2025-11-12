# stepper_class_shiftregister_multiprocessing.py
#
# Stepper class – parallel control of multiple steppers via shift register(s)
# Edits for Lab 8:
#  - fine-grained locking (simultaneous motion)
#  - correct per-motor bit masking in __step
#  - multiprocessing.Value for angle (shared across processes)
#  - goAngle() shortest-path move

import time
import multiprocessing
from shifter import Shifter   # your Lab 6 class

class Stepper:
    """
    Supports N stepper motors via one or more shift registers.

    Motors are packed 4 bits each. For 2 motors, motor 2 uses Qa–Qd,
    motor 1 uses Qe–Qh (MSB near Qa). See comments in starter.
    """

    # ----- class attributes -----
    num_steppers      = 0
    shifter_outputs   = 0
    # half-step CCW sequence (as in starter)
    seq               = [0b0001,0b0011,0b0010,0b0110,0b0100,0b1100,0b1000,0b1001]
    delay_us          = 1200                     # time between steps [µs]
    steps_per_degree  = 4096/360                 # 4096 steps / rev

    def __init__(self, shifter, lock):
        self.s = shifter
        # angle must be shared across processes -> multiprocessing.Value
        self.angle = multiprocessing.Value('d', 0.0)
        self.step_state = 0
        self.shifter_bit_start = 4 * Stepper.num_steppers
        self.lock = lock
        Stepper.num_steppers += 1

    # ----- helpers -----
    @staticmethod
    def __sgn(x):
        if x == 0:
            return 0
        return 1 if x > 0 else -1

    def __write_outputs(self, new_4bit_value):
        """
        Atomically replace this motor's 4 bits in the shared output image,
        then shift the byte out. Lock is held only during the critical section.
        """
        with self.lock:
            # Clear my 4 bits, then OR in the new 4-bit pattern at my bit start.
            clear_mask = ~(0b1111 << self.shifter_bit_start) & 0xFF
            Stepper.shifter_outputs = (Stepper.shifter_outputs & clear_mask) | \
                                      ((new_4bit_value & 0b1111) << self.shifter_bit_start)
            self.s.shiftByte(Stepper.shifter_outputs)

    # ----- one step in +/- direction -----
    def __step(self, dir_sign):
        self.step_state = (self.step_state + dir_sign) % 8
        pat = Stepper.seq[self.step_state]
        self.__write_outputs(pat)

        # Update shared angle
        with self.angle.get_lock():
            self.angle.value = (self.angle.value + dir_sign/Stepper.steps_per_degree) % 360.0

    # ----- relative move (runs inside a process) -----
    def __rotate(self, delta):
        num_steps = int(abs(delta) * Stepper.steps_per_degree)
        dir_sign  = Stepper.__sgn(delta)
        for _ in range(num_steps):
            self.__step(dir_sign)
            time.sleep(Stepper.delay_us/1e6)

    # ----- public async relative move -----
    def rotate(self, delta):
        # separate process so calls to different motors can overlap
        p = multiprocessing.Process(target=self.__rotate, args=(delta,))
        p.start()

    # ----- absolute move by shortest path -----
    def goAngle(self, target_deg):
        # normalize target
        t = float(target_deg) % 360.0
        with self.angle.get_lock():
            c = self.angle.value % 360.0
        # shortest signed delta in (-180, 180]
        delta = ((t - c + 180.0) % 360.0) - 180.0
        self.rotate(delta)

    # ----- zero reference -----
    def zero(self):
        with self.angle.get_lock():
            self.angle.value = 0.0


# ---------------- Example / Demo ----------------
if __name__ == '__main__':
    # Shifter pins: data=16, latch=20, clock=21 (from your earlier labs)
    s = Shifter(data=16, latch=20, clock=21)

    # One lock shared by all motors: protects only the SPI/shift operation
    lock = multiprocessing.Lock()

    # Instantiate two motors (m1, m2). Bit packing follows class comment.
    m1 = Stepper(s, lock)
    m2 = Stepper(s, lock)

    # Zero both
    m1.zero()
    m2.zero()

    # ---- Lab 8 step 4: demo sequence (simultaneous behavior) ----
    # If implemented correctly, sequential calls below cause both motors
    # to move at the same time because each call spawns its own process
    # and the lock is held only during single-byte writes.

    # 1) zero positions already done above

    # 2) m1
    m1.goAngle(90)
    m1.goAngle(-45)

    # 3) m2
    m2.goAngle(-90)
    m2.goAngle(45)

    # 4) shortest-path test on m1
    m1.goAngle(-135)
    m1.goAngle(135)
    m1.goAngle(0)

    # keep main alive while child processes run
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print('\nend')