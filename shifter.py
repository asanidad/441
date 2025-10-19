# ENME 441 – Lab 6
# Shifter class for SN74HC595 (controls 8 LEDs using 3 GPIO pins)
# Uses BCM numbering, matches the shift-register slides.

import RPi.GPIO as GPIO

class Shifter:
    def __init__(self, serialPin, clockPin, latchPin):
        self.serialPin = serialPin
        self.clockPin  = clockPin
        self.latchPin  = latchPin

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.serialPin, GPIO.OUT)
        GPIO.setup(self.clockPin,  GPIO.OUT)
        GPIO.setup(self.latchPin,  GPIO.OUT)

        # start with LEDs off
        self.shiftByte(0)

    # private helper: one clock pulse to shift a bit in
    def _ping(self):
        GPIO.output(self.clockPin, 1)
        GPIO.output(self.clockPin, 0)

    # public: send one byte (0..255) to Q0..Q7, MSB first
    def shiftByte(self, data):
        data &= 0xFF
        GPIO.output(self.latchPin, 0)           # hold latch low while shifting
        for i in range(8):
            bit = (data >> (7 - i)) & 1         # MSB first (matches class demo)
            GPIO.output(self.serialPin, bit)
            self._ping()
        GPIO.output(self.latchPin, 1)           # latch updates Q0..Q7

    # optional helper I used for cleanup
    def clear(self):
        self.shiftByte(0)
