# stepper_class_shiftregister_multiprocessing.py
# Integer-step Stepper (low/high nibble of 74HC595) + SyncController, with invert flag.

import time
from multiprocessing import Value

class Stepper:
    """
    Full-step 4-phase stepper tied to either the low or high nibble of the 74HC595.
    Tracks position in integer steps (no float drift). Angle is derived for display.
    nibble: 'low'  -> Q0..Q3
            'high' -> Q4..Q7
    invert: True reverses the motor direction (software flip)
    """
    _seq     = (0b0001, 0b0010, 0b0100, 0b1000)     # A, B, C, D
    _seq_inv = tuple(reversed(_seq))                # D, C, B, A

    def __init__(self, nibble: str, steps_per_rev: int = 2048, step_delay: float = 0.012,
                 invert: bool = False):
        assert nibble in ('low', 'high')
        self.nibble = nibble
        self.steps_per_rev = int(steps_per_rev)
        self.step_delay = float(step_delay)
        self.invert = bool(invert)

        # integer step state
        self.step_pos = 0          # absolute step index
        self.target_step = 0       # absolute step index target

        # angle “view” (derived from step_pos)
        self.angle = Value('d', 0.0)
        self._deg_per_step = 360.0 / self.steps_per_rev

    # ---------- helpers ----------
    def _phase_index(self) -> int:
        return self.step_pos & 0x3  # % 4

    def coil_mask_now(self) -> int:
        # choose forward or reversed coil sequence
        nib = (Stepper._seq_inv if self.invert else Stepper._seq)[self._phase_index()]
        return (nib if self.nibble == 'low' else (nib << 4)) & 0xFF

    def _update_angle_view(self):
        self.angle.value = self.step_pos * self._deg_per_step

    # ---------- API ----------
    def zero(self):
        self.step_pos = 0
        self.target_step = 0
        self._update_angle_view()

    def set_target(self, target_deg: float):
        """Set absolute target angle (deg) using shortest-path in step space."""
        tgt_nom = int(round(target_deg / self._deg_per_step))
        cur = self.step_pos % self.steps_per_rev
        tgt = tgt_nom % self.steps_per_rev
        delta = tgt - cur
        half = self.steps_per_rev // 2
        if delta >  half: delta -= self.steps_per_rev
        if delta < -half: delta += self.steps_per_rev
        self.target_step = self.step_pos + delta

    def at_target(self) -> bool:
        return self.step_pos == self.target_step

    def step_toward_target(self) -> bool:
        if self.at_target():
            return False
        self.step_pos += 1 if self.target_step > self.step_pos else -1
        self._update_angle_view()
        return True


class SyncController:
    """
    Drives multiple Stepper instances in lock-step timing. On each tick:
      - each motor that still needs to move advances by one step
      - compose a single 8-bit byte (Q7..Q0) and shift it once to the 74HC595
    Pass in a Shifter instance that exposes shiftByte(byte: int).
    """
    def __init__(self, shifter):
        self.s = shifter

    def run_until_all_reached(self, motors):
        delay = max(m.step_delay for m in motors) if motors else 0.01
        while True:
            if all(m.at_target() for m in motors):
                # keep holding coils at final phases
                b = 0
                for m in motors: b |= m.coil_mask_now()
                self.s.shiftByte(b)
                break

            # step any motor that still has distance to go
            for m in motors:
                m.step_toward_target()

            # one write for all coils (low nibble = motor on Q0..Q3, high nibble = Q4..Q7)
            b = 0
            for m in motors: b |= m.coil_mask_now()
            self.s.shiftByte(b)

            time.sleep(delay)
