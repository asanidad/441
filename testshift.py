# test_shift_halfstep.py  (run: python3 test_shift_halfstep.py)
import time
from stepper_class_shiftregister_multiprocessing import Shifter

# Use the same order your Shifter expects. You said this worked best:
s = Shifter(16, 21, 20)   # SER=16, CLOCK=21, LATCH=20  (if no motion, also try Shifter(16,20,21))

def write_byte(b):
    # The course Shifter usually has a write(raw_byte) or shiftOut+Latch pair.
    # If your class has a method named 'shift'/'write', call that.
    s.shiftOut(b)     # if your class uses s.shift(b) or s.write(b), change this line accordingly
    s.latch()

# Half-step pattern for motor 1 on Q0..Q3 (low nibble). Motor 2 off (high nibble=0).
pat = [0b0001,0b0011,0b0010,0b0110,0b0100,0b1100,0b1000,0b1001]

try:
    while True:
        for p in pat:
            write_byte(p)        # Motor1 on Q0..Q3
            time.sleep(0.02)     # slower = easier to see
except KeyboardInterrupt:
    write_byte(0)
