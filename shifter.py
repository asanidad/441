import RPi.GPIO as GPIO

class Shifter:
    def __init__(self, dataPin=23, latchPin=24, clockPin=25):
        self.dataPin  = dataPin
        self.latchPin = latchPin
        self.clockPin = clockPin

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.dataPin,  GPIO.OUT)
        GPIO.setup(self.latchPin, GPIO.OUT, initial=0)
        GPIO.setup(self.clockPin, GPIO.OUT, initial=0)

        self.shiftByte(0) # clear LEDs at start

    def _ping(self): # one clock pulse
        GPIO.output(self.clockPin, 1)
        GPIO.output(self.clockPin, 0)

    def shiftByte(self, pattern): # send 8 bits to shift register
        pattern &= 0xFF
        GPIO.output(self.latchPin, 0)
        for i in range(8):
            bit = (pattern >> i) & 1
            GPIO.output(self.dataPin, bit)
            self._ping()
        GPIO.output(self.latchPin, 1)
        GPIO.output(self.latchPin, 0)

    def clear(self):
        self.shiftByte(0)
