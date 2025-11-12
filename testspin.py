# test_one_motor_spin.py
import time
from stepper_class_shiftregister_multiprocessing import Shifter

# Use the same working pin order you just validated with the chase:
s = Shifter(16, 21, 20)   # or Shifter(16, 20, 21) if that was your “good” order

def write_byte(b):
    s.shiftOut(b)   # use the Shifter's shift method
    s.latch()

# Half-step sequence on the LOW nibble (motor 1: Q0..Q3) in ABCD order
seq = [0b0001, 0b0011, 0b0010, 0b0110, 0b0100, 0b1100, 0b1000, 0b1001]

try:
    for k in range(3):                 # 3 revolutions-ish at slow speed
        for p in seq:
            write_byte(p)              # motor 1
            time.sleep(0.01)           # 10 ms per half-step; increase if it skips
finally:
    write_byte(0)
