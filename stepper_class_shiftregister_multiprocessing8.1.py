# stepper_class_shiftregister_multiprocessing.py
# ENME441 – Stepper control via 74HC595 shift register
# One file with Shifter + Stepper. Motors step simultaneously on each tick.

import time
import RPi.GPIO as GPIO

# -------------------- basic hardware setup --------------------
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# 74HC595 pins (BCM)
DEFAULT_DATA  = 16
DEFAULT_LATCH = 20
DEFAULT_CLOCK = 21

# 28BYJ-48 defaults (half-step)
STEPS_PER_REV = 4096          # adjust if you calibrated
STEP_DELAY_S  = 0.003         # speed (larger = slower)
DIR_SIGN      = +1            # flip to -1 if your “+deg” looks backwards

# half-step nibble sequence for one motor (A,B,C,D on bits 0..3)
SEQ = (0x1, 0x3, 0x2, 0x6, 0x4, 0xC, 0x8, 0x9)
SEQ_LEN = len(SEQ)


# -------------------- helpers --------------------
def shortest_delta_deg(a, b):
    """signed shortest delta from angle a to b (-180..+180]"""
    d = (b - a) % 360.0
    if d > 180.0:
        d -= 360.0
    return d

def degrees_to_steps(deg, spr=STEPS_PER_REV):
    return int(round((deg / 360.0) * spr))

def steps_to_degrees(steps, spr=STEPS_PER_REV):
    return (steps * 360.0) / float(spr)


# -------------------- Shifter --------------------
class Shifter:
    """Tiny 74HC595 driver (MSB-first). Also holds the list of motors so we can step them together."""
    def __init__(self, data=DEFAULT_DATA, latch=DEFAULT_LATCH, clock=DEFAULT_CLOCK):
        self.data  = data
        self.latch = latch
        self.clock = clock
        for p in (self.data, self.latch, self.clock):
            GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)
        self._motors = []   # Stepper objects registered here

    def register(self, motor):
        if motor not in self._motors:
            self._motors.append(motor)

    def shiftByte(self, byte):
        GPIO.output(self.latch, GPIO.LOW)
        # MSB first
        for bit in range(7, -1, -1):
            GPIO.output(self.clock, GPIO.LOW)
            GPIO.output(self.data, GPIO.HIGH if ((byte >> bit) & 1) else GPIO.LOW)
            GPIO.output(self.clock, GPIO.HIGH)
        GPIO.output(self.latch, GPIO.HIGH)

    def _any_pending(self):
        return any(m._steps_left > 0 for m in self._motors)

    def run_until_idle(self, step_delay=STEP_DELAY_S):
        """Step all registered motors together until every one completes its pending motion."""
        while self._any_pending():
            # advance those that still need a step
            for m in self._motors:
                if m._steps_left > 0:
                    m._step_once()
            # pack both nibbles into one byte and output once per tick
            b = 0
            for m in self._motors:
                b |= m._nibble()
            self.shiftByte(b)
            time.sleep(step_delay)
        # Done -> update final angles and optionally de-energize
        for m in self._motors:
            if m._accum_steps != 0:
                m.angle = (m.angle + steps_to_degrees(m._accum_steps / DIR_SIGN, m.steps_per_rev)) % 360.0
                m._accum_steps = 0
        # comment next line if you prefer holding torque after a move
        # self.shiftByte(0x00)


# -------------------- Stepper --------------------
class Stepper:
    """One 28BYJ-48 on one nibble of the shift-register byte."""
    def __init__(self, shifter, use_high_nibble=False, steps_per_rev=STEPS_PER_REV):
        self.s = shifter
        self.s.register(self)
        self.use_high = bool(use_high_nibble)  # False = low nibble, True = high nibble
        self.steps_per_rev = int(steps_per_rev)

        self.seq_idx     = 0
        self.angle       = 0.0     # logical angle (deg) relative to zero()
        self._steps_left = 0       # pending steps for current command
        self._dir        = +1
        self._accum_steps = 0      # total scheduled this burst (used to update angle once)

    # current coil nibble
    def _nibble(self):
        val = SEQ[self.seq_idx]
        return (val << 4) & 0xF0 if self.use_high else (val & 0x0F)

    # perform one step in the queued direction
    def _step_once(self):
        self.seq_idx = (self.seq_idx + (1 if self._dir > 0 else -1)) % SEQ_LEN
        self._steps_left -= 1

    # user API
    def zero(self):
        self.angle = 0.0

    def setSpeed(self, step_delay_s):
        global STEP_DELAY_S
        STEP_DELAY_S = float(step_delay_s)

    def rotate(self, deg):
        """Relative rotation (deg). This only *queues* the move; after queueing several
        motors, call shifter.run_until_idle() to move them together."""
        # respect chosen “+deg” direction convention
        deg *= DIR_SIGN
        n = abs(degrees_to_steps(deg, self.steps_per_rev))
        self._dir = +1 if deg >= 0 else -1
        self._steps_left += n
        self._accum_steps += self._dir * n

    def goAngle(self, target_deg):
        """Shortest-path move to an absolute angle (deg) relative to zero()."""
        delta = shortest_delta_deg(self.angle, target_deg)
        self.rotate(delta)


# -------------------- Demo (runs the required sequence) --------------------
def _demo():
    s  = Shifter()                          # default pins 16,20,21
    m1 = Stepper(s, use_high_nibble=False)  # low nibble
    m2 = Stepper(s, use_high_nibble=True)   # high nibble

    # speed tweak if needed:
    # m1.setSpeed(0.004); m2.setSpeed(0.004)

    # logical zeros
    m1.zero(); m2.zero()

    # The trick for “simultaneous” is: queue both motors’ moves, then call run_until_idle() once.

    # m1: +90 then -45
    m1.rotate(+90);            s.run_until_idle()      # queue + run
    m1.rotate(-45);            s.run_until_idle()

    # m2: -90 then +45
    m2.rotate(-90);            s.run_until_idle()
    m2.rotate(+45);            s.run_until_idle()

    # m1: -135, +135, 0
    m1.rotate(-135);           s.run_until_idle()
    m1.rotate(+135);           s.run_until_idle()
    m1.goAngle(0);             s.run_until_idle()

    # release coils at the end (optional)
    s.shiftByte(0x00)

if __name__ == "__main__":
    try:
        _demo()
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
