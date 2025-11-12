# stepper_class_shiftregister_multiprocessing.py
# ENME441 – Lab 8 (Simultaneous stepper motion using one 74HC595)

import RPi.GPIO as GPIO
import time
from multiprocessing import Value

# ==========================
# Shift register (74HC595)
# ==========================
class Shifter:
    """
    74HC595 driver. Use shiftByte(b) to output 8 bits to Q7..Q0.
    """
    def __init__(self, serialPin: int, latchPin: int, clockPin: int):
        self.ser = serialPin
        self.latch = latchPin
        self.clk = clockPin

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.ser, GPIO.OUT, initial=0)
        GPIO.setup(self.latch, GPIO.OUT, initial=0)
        GPIO.setup(self.clk, GPIO.OUT, initial=0)

    def _pulse(self, pin: int):
        GPIO.output(pin, 1)
        GPIO.output(pin, 0)

    def shiftByte(self, value: int):
        """
        Send 8 bits MSB→LSB to the 74HC595, then latch.
        """
        value &= 0xFF
        # shift out MSB first (Q7..Q0)
        for bit in range(7, -1, -1):
            GPIO.output(self.ser, (value >> bit) & 1)
            self._pulse(self.clk)
        self._pulse(self.latch)


# ==========================
# Stepper (full-step, 4-phase)
# ==========================
class Stepper:
    """
    Full-step 4-phase stepper tied to either the low or high nibble of the 74HC595.
    angle is stored in a multiprocessing.Value so other processes could read it if needed.
    """
    # ABCD sequence (one coil at a time)
    _seq = (0b0001, 0b0010, 0b0100, 0b1000)

    def __init__(self, nibble: str, steps_per_rev: int = 200, step_delay: float = 0.003):
        """
        nibble: 'low' → Q0..Q3, 'high' → Q4..Q7
        steps_per_rev: adjust to your motors (200 is typical for 1.8°/step full-step)
        step_delay: time per step (seconds)
        """
        assert nibble in ('low', 'high')
        self.nibble = nibble
        self.steps_per_rev = steps_per_rev
        self.step_delay = step_delay

        self._phase = 0                # index in _seq
        self.angle = Value('d', 0.0)    # current angle (deg), safe to share
        self._target_deg = 0.0          # where we want to go (deg)

        # cached
        self._deg_per_step = 360.0 / float(steps_per_rev)

    # ----------------------
    # helpers / state
    # ----------------------
    def zero(self):
        self.angle.value = 0.0
        self._target_deg = 0.0
        self._phase = 0

    def set_target(self, new_angle_deg: float):
        """Queue a new absolute target angle (deg) to be reached."""
        self._target_deg = float(new_angle_deg)

    def at_target(self) -> bool:
        # use step-space to avoid float drift
        return self._delta_steps() == 0

    def coil_mask_now(self) -> int:
        """Return the nibble (4 bits) to energize at this moment."""
        n = Stepper._seq[self._phase]
        return (n if self.nibble == 'low' else (n << 4)) & (0x0F if self.nibble == 'low' else 0xF0)

    # ----------------------
    # stepping math
    # ----------------------
    def _round_to_step(self, deg: float) -> int:
        return int(round(deg / self._deg_per_step))

    def _delta_steps(self) -> int:
        """
        Steps needed (with shortest path). Positive → forward (phase +1),
        Negative → reverse (phase -1).
        """
        cur_steps = self._round_to_step(self.angle.value)
        tgt_steps = self._round_to_step(self._target_deg)
        raw = tgt_steps - cur_steps

        # wrap into shortest path over the full revolution
        half_rev = self.steps_per_rev // 2
        if raw > half_rev:
            raw -= self.steps_per_rev
        elif raw < -half_rev:
            raw += self.steps_per_rev
        return raw

    def step_toward_target(self) -> bool:
        """
        Take one step toward target if needed.
        Returns True if a step occurred (i.e., still moving).
        """
        ds = self._delta_steps()
        if ds == 0:
            return False

        if ds > 0:
            # forward
            self._phase = (self._phase + 1) % 4
            self.angle.value += self._deg_per_step
        else:
            # reverse
            self._phase = (self._phase - 1) % 4
            self.angle.value -= self._deg_per_step
        return True


# ==========================
# Synchronous controller
# ==========================
class SyncController:
    """
    Drives multiple Stepper instances in lock-step (same timing loop).
    Each loop iteration computes the combined 8-bit coil mask (Q7..Q0) and shifts once.
    This makes motors move *simultaneously* even though you set the targets separately.
    """
    def __init__(self, shifter: Shifter):
        self.s = shifter

    def run_until_all_reached(self, motors: list[Stepper]):
        """
        Step loop: on each iteration, any motor that still has distance
        to go takes one step; others hold their coil. Then we output the
        merged byte and sleep using the *slowest* motor's step delay.
        """
        # choose a conservative delay (largest step_delay among the group)
        delay = max(m.step_delay for m in motors)

        while True:
            # check if all are already at target
            if all(m.at_target() for m in motors):
                # still need to energize holding coils at the final phases
                b = 0
                for m in motors:
                    b |= m.coil_mask_now()
                self.s.shiftByte(b)
                break

            # move one step for each motor that still needs to go
            for m in motors:
                m.step_toward_target()

            # build and output the merged nibble byte
            b = 0
            for m in motors:
                b |= m.coil_mask_now()
            self.s.shiftByte(b)

            time.sleep(delay)
