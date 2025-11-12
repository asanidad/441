# testspin.py
# Simple half-step test for one stepper motor via 74HC595

import time
from stepper_class_shiftregister_multiprocessing import Shifter

# Create shifter with your known-good wiring
# Arguments follow (dataPin, latchPin, clockPin)
s = Shifter(16, 20, 21)   # use the same order you used in lab8.py

def write_byte(b: int):
    s.shiftByte(b & 0xFF)   # send byte to the 595 (auto-latch handled in class)

# Half-step sequence (ABCD order, low nibble)
seq = [0b0001, 0b0011, 0b0010, 0b0110,
       0b0100, 0b1100, 0b1000, 0b1001]

try:
    print("Spinning motor 1 (low nibble)... CTRL-C to stop.")
    while True:
        for p in seq:
            write_byte(p)
            time.sleep(0.01)  # adjust to ~0.015–0.02 if it jitters
finally:
    write_byte(0)  # all coils off
