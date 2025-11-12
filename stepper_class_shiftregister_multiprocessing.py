# stepper_class_shiftregister_multiprocessing.py
# 74HC595 shifter + very small Stepper class (full-step, 4-phase)
# Uses two 4-bit nibbles of one shift register: low nibble = motor1, high nibble = motor2

import time
import math
import RPi.GPIO as GPIO


# ----------------------------
# 74HC595 helper (one register)
# ----------------------------
class Shifter:
    def __init__(self, data_pin: int, latch_pin: int, clock_pin: int):
        self.data = data_pin
        self.latch = latch_pin
        self.clock = clock_pin

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.data, GPIO.OUT, initial=0)
        GPIO.setup(self.latch, GPIO.OUT, initial=0)
        GPIO.setup(self.clock, GPIO.OUT, initial=0)

        self._last = 0  # last latched byte (so we can change only one nibble)

    def _pulse(self, pin):
        GPIO.output(pin, 1)
        GPIO.output(pin, 0)

    def shiftByte(self, b: int):
        """Shift out one byte MSB-first, then latch."""
        b &= 0xFF
        for i in range(7, -1, -1):
            GPIO.output(self.data, (b >> i) & 1)
            self._pulse(self.clock)
        # latch to outputs
        GPIO.output(self.latch, 1)
        GPIO.output(self.latch, 0)
        self._last = b

    def write_nibble(self, which: str, val: int):
        """Update only a nibble ('low' or 'high') and keep the other nibble as-is."""
        val &= 0x0F
        if which == 'low':
            newb = (self._last & 0xF0) | val
        else:  # 'high'
            newb = (self._last & 0x0F) | (val << 4)
        self.shiftByte(newb)


# ----------------------------
# Stepper (full-step sequence)
# ----------------------------
class Stepper:
    # Full-step sequence (ABCD)
    _SEQ_FULL = (0x1, 0x2, 0x4, 0x8)

    def __init__(self,
                 shifter: Shifter,
                 nibble: str = 'low',
                 mode: str = 'full',
                 step_angle_deg: float = 1.8,
                 step_delay_s: float = 0.003):
        """
        nibble: 'low' -> Q0..Q3, 'high' -> Q4..Q7
        mode:   currently only 'full' is implemented (4 phases)
        """
        self.s = shifter
        self.nibble = 'low' if nibble.lower().startswith('l') else 'high'
        self.mode = mode
        self.step_angle = float(step_angle_deg)
        self.delay = float(step_delay_s)

        self._seq = Stepper._SEQ_FULL
        self._idx = 0  # current index in sequence
        self.angle = 0.0  # software-tracked absolute angle (deg)

        # turn off initially
        self._write_coils(0)

    # ---- low-level ----
    def _write_coils(self, val4):
        self.s.write_nibble(self.nibble, val4 & 0x0F)

    def _step_once(self, direction: int):
        # direction: +1 or -1
        self._idx = (self._idx + direction) % len(self._seq)
        self._write_coils(self._seq[self._idx])
        time.sleep(self.delay)

    # ---- public API ----
    def step(self, steps: int):
        """Number of full steps; positive = CW, negative = CCW (depends on wiring)."""
        direction = 1 if steps >= 0 else -1
        for _ in range(abs(int(steps))):
            self._step_once(direction)
        # deenergize after motion (safer for bench power)
        self._write_coils(0)

    def rotate(self, deg: float):
        """Rotate by a relative angle in degrees."""
        steps_per_rev = 360.0 / self.step_angle
        steps = int(round(deg * steps_per_rev / 360.0 * 360.0 / self.step_angle))
        # equivalently: steps = int(round(deg / self.step_angle))
        self.step(steps)
        self.angle = self._norm_angle(self.angle + deg)

    def zero(self):
        """Set current position as 0° (software only)."""
        self.angle = 0.0

    def goAngle(self, target_deg: float):
        """
        Go to absolute angle using the shortest path (−180..+180).
        target is relative to the zero() reference.
        """
        cur = self._norm_angle(self.angle)
        tgt = self._norm_angle(target_deg)
        delta = tgt - cur
        # wrap to shortest path
        if delta > 180.0:
            delta -= 360.0
        elif delta < -180.0:
            delta += 360.0
        self.rotate(delta)

    # ---- helpers ----
    @staticmethod
    def _norm_angle(a):
        # normalize to [0, 360)
        a = math.fmod(a, 360.0)
        if a < 0:
            a += 360.0
        return a


# Optional: tiny self-test (won't run when imported)
if __name__ == "__main__":
    GPIO.setwarnings(False)
    try:
        sh = Shifter(16, 20, 21)
        m1 = Stepper(sh, nibble='low')
        m1.zero()
        m1.goAngle(90)
        m1.goAngle(0)
    finally:
        GPIO.cleanup()
