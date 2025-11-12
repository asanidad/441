# test_595_chase.py
import RPi.GPIO as GPIO, time

# CHANGE these to your wires from the Pi:
SER   = 16  # to 74HC595 DS (pin 14)
CLOCK = 21  # to 74HC595 SHCP (pin 11)  <-- shift clock
LATCH = 20  # to 74HC595 STCP (pin 12)  <-- output latch

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(SER, GPIO.OUT); GPIO.setup(CLOCK, GPIO.OUT); GPIO.setup(LATCH, GPIO.OUT)
GPIO.output(SER, 0); GPIO.output(CLOCK, 0); GPIO.output(LATCH, 0)

def pulse(pin):
    GPIO.output(pin, 1); time.sleep(0.001); GPIO.output(pin, 0)

def shift_byte(val):
    # MSB-first or LSB-first depends on your class; this is LSB-first (common in class slides)
    for i in range(8):
        GPIO.output(SER, (val >> i) & 1)
        pulse(CLOCK)     # load the bit into the shift register
    pulse(LATCH)         # present the 8 bits on Q0..Q7

try:
    while True:
        for i in range(8):
            shift_byte(1 << i)   # Q0 -> Q7
            time.sleep(0.1)
except KeyboardInterrupt:
    shift_byte(0)
    GPIO.cleanup()
