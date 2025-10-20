# ENME 441 – Lab 6
# Shifter class for SN74HC595 using the same pin roles as shift_reg_initial.py
# dataPin=23, latchPin=24, clockPin=25  (BCM numbering)

import RPi.GPIO as GPIO

class Shifter:
    def __init__(self, dataPin=23, latchPin=24, clockPin=25):
        self.dataPin  = dataPin
        self.latchPin = latchPin
        self.clockPin = clockPin

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.dataPin,  GPIO.OUT)
        GPIO.setup(self.latchPin, GPIO.OUT, initial=0)   # start low like the class code
        GPIO.setup(self.clockPin, GPIO.OUT, initial=0)

        # start with everything off
        self.shiftByte(0)

    # --- private helper: one rising-edge pulse on the shift clock ---
    def _ping(self):
        GPIO.output(self.clockPin, 1)
        GPIO.output(self.clockPin, 0)

    # --- public: shift one byte into the register, LSB-first (matches class code) ---
    def shiftByte(self, pattern):
        """Send 8 bits to the 74HC595 and latch them to Q0..Q7.
           LSB-first to mirror: pattern & (1<<i) in shift_reg_initial.py.
        """
        pattern &= 0xFF

        # hold latch low while shifting (same as class code)
        GPIO.output(self.latchPin, 0)

        # LSB-first, exactly like: pattern & (1<<i)
        for i in range(8):
            bit = (pattern >> i) & 1
            GPIO.output(self.dataPin, bit)
            self._ping()

        # latch to outputs
        GPIO.output(self.latchPin, 1)
        GPIO.output(self.latchPin, 0)

    def clear(self):
        self.shiftByte(0)
