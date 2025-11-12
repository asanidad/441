# testspin_tuned.py
# Spin one 28BYJ-48 smoothly via 74HC595 -> ULN2003, with speed/ramp options

import time
from stepper_class_shiftregister_multiprocessing import Shifter

# ---- wiring (same order you used in lab8.py) ----
s = Shifter(16, 20, 21)   # (data, latch, clock)

def out(b):
    s.shiftByte(b & 0xFF)  # lower nibble -> motor 1 coils

# Sequences for one motor on the LOW nibble (bits 0..3).
# If your board is wired so the low nibble goes to the other motor, swap nibbles.
SEQ_HALF = [0b0001, 0b0011, 0b0010, 0b0110,
            0b0100, 0b1100, 0b1000, 0b1001]  # A,B,C,D half-step

SEQ_FULL = [0b0011, 0b0110, 0b1100, 0b1001]  # AB,BC,CD,DA full-step

MODE = "full"       # "full" or "half"
TARGET_DELAY = 0.0025   # seconds between steps at speed (≈ 2.5 ms)
START_DELAY  = 0.008    # begin slower so it can start moving
RAMP_STEPS   = 300      # how many steps to ramp down to target
RUN_STEPS    = 4000     # additional steps at steady speed
PAUSE        = 0.3

seq = SEQ_FULL if MODE == "full" else SEQ_HALF

try:
    print(f"Mode={MODE}, start_delay={START_DELAY*1000:.1f}ms "
          f"→ target={TARGET_DELAY*1000:.1f}ms")

    # accelerate
    delay = START_DELAY
    for i in range(RAMP_STEPS):
        out(seq[i % len(seq)])
        time.sleep(delay)
        # linear ramp toward target delay
        delay = START_DELAY + (TARGET_DELAY - START_DELAY) * (i / RAMP_STEPS)

    # run at target speed
    for i in range(RUN_STEPS):
        out(seq[i % len(seq)])
        time.sleep(TARGET_DELAY)

    # brief stop
    out(0)
    time.sleep(PAUSE)

    # reverse demonstration (optional)
    for i in range(RAMP_STEPS):
        out(seq[-(i % len(seq)) - 1])
        time.sleep(TARGET_DELAY)

finally:
    out(0)  # coils off
