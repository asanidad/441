import time
from multiprocessing import Value
from shifter import Shifter as CourseShifter  # provided by the professor
import RPi.GPIO as GPIO

# helpers
def _rev8(b: int) -> int:
    b &= 0xFF
    b = ((b & 0xF0) >> 4) | ((b & 0x0F) << 4)
    b = ((b & 0xCC) >> 2) | ((b & 0x33) << 2)
    b = ((b & 0xAA) >> 1) | ((b & 0x55) << 1)
    return b

# motor class
class Stepper:
    # full-step (single coil) sequence; invert=True flips direction
    _seq     = (0b0001, 0b0010, 0b0100, 0b1000)     # A B C D
    _seq_inv = tuple(reversed(_seq))                # D C B A

    def __init__(self, nibble: str, steps_per_rev: int = 2048,
                 step_delay: float = 0.012, invert: bool = False):
        assert nibble in ("low", "high")
        self.nibble = nibble
        self.steps_per_rev = int(steps_per_rev)
        self.step_delay = float(step_delay)
        self.invert = bool(invert)

        # track position as integer steps (avoids float rounding)
        self.step_pos = 0
        self.target_step = 0

        # angle view (shared-friendly)
        self.angle = Value('d', 0.0)
        self._deg_per_step = 360.0 / self.steps_per_rev

    # current 4-phase index (0..3)
    def _phase_index(self) -> int:
        return self.step_pos & 0x3

    # return this motor's 8-bit mask in the shared output byte
    def coil_mask_now(self) -> int:
        phase = (Stepper._seq_inv if self.invert else Stepper._seq)[self._phase_index()]
        return (phase if self.nibble == "low" else (phase << 4)) & 0xFF

    def _update_angle_view(self):
        self.angle.value = self.step_pos * self._deg_per_step

    def zero(self):
        self.step_pos = 0
        self.target_step = 0
        self._update_angle_view()

    # absolute move to angle a (deg) using shortest path
    def goAngle(self, a: float):
        tgt_nom = int(round(a / self._deg_per_step))
        cur_mod = self.step_pos % self.steps_per_rev
        tgt_mod = tgt_nom % self.steps_per_rev
        delta = tgt_mod - cur_mod
        half = self.steps_per_rev // 2
        if delta >  half: delta -= self.steps_per_rev
        if delta < -half: delta += self.steps_per_rev
        self.target_step = self.step_pos + delta

    def at_target(self) -> bool:
        return self.step_pos == self.target_step

    # one step toward target (returns True if stepped)
    def step_toward_target(self) -> bool:
        if self.at_target():
            return False
        self.step_pos += 1 if self.target_step > self.step_pos else -1
        self._update_angle_view()
        return True


# controller for motor lockstep
class SyncController:
    def __init__(self, data_pin: int, latch_pin: int, clock_pin: int):
        self.s = CourseShifter(data=data_pin, latch=latch_pin, clock=clock_pin)

    def _push_byte(self, b: int):
        # the course shifter clocks LSB-first, so reverse once here
        self.s.shiftByte(_rev8(b))

    def run_until_all_reached(self, motors):
        delay = max(m.step_delay for m in motors) if motors else 0.01
        while True:
            # if already at targets, still refresh outputs so coils are held
            if all(m.at_target() for m in motors):
                out = 0
                for m in motors: out |= m.coil_mask_now()
                self._push_byte(out)
                break

            # take one step on whichever still needs it
            for m in motors:
                m.step_toward_target()

            # combine the two nibbles and send one byte
            out = 0
            for m in motors: out |= m.coil_mask_now()
            self._push_byte(out)

            time.sleep(delay)


# question 4 demonstration
SER_PIN   = 16   # BCM
LATCH_PIN = 20
CLOCK_PIN = 21
STEPS_PER_REV = 2048    # 28BYJ-48 full-step
STEP_DELAY    = 0.012
INVERT_M1     = True
INVERT_M2     = True

def _demo_sequence():
    ctrl = SyncController(SER_PIN, LATCH_PIN, CLOCK_PIN)

    # motor 1 on low nibble; motor 2 on high nibble
    m1 = Stepper("low",  steps_per_rev=STEPS_PER_REV, step_delay=STEP_DELAY, invert=INVERT_M1)
    m2 = Stepper("high", steps_per_rev=STEPS_PER_REV, step_delay=STEP_DELAY, invert=INVERT_M2)

    print("Zero both…")
    m1.zero(); m2.zero()
    ctrl.run_until_all_reached([m1, m2]); time.sleep(0.4)

    try:
        print("m1.goAngle(90)")
        m1.goAngle(90);    ctrl.run_until_all_reached([m1, m2]); time.sleep(0.4)

        print("m1.goAngle(-45)")
        m1.goAngle(-45);   ctrl.run_until_all_reached([m1, m2]); time.sleep(0.4)

        print("m2.goAngle(-90)")
        m2.goAngle(-90);   ctrl.run_until_all_reached([m1, m2]); time.sleep(0.4)

        print("m2.goAngle(45)")
        m2.goAngle(45);    ctrl.run_until_all_reached([m1, m2]); time.sleep(0.4)

        print("m1.goAngle(-135)")
        m1.goAngle(-135);  ctrl.run_until_all_reached([m1, m2]); time.sleep(0.4)

        print("m1.goAngle(135)")
        m1.goAngle(135);   ctrl.run_until_all_reached([m1, m2]); time.sleep(0.4)

        print("m1.goAngle(0)")
        m1.goAngle(0);     ctrl.run_until_all_reached([m1, m2]); time.sleep(0.4)

        print("Done.")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    _demo_sequence()