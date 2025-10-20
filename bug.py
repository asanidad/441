# ENME 441 – Lab 6
# Bug class + main loop using SN74HC595 via Shifter (data=23, latch=24, clock=25)

import time
import random
import RPi.GPIO as GPIO
from shifter import Shifter

# ------------------ Bug class ------------------

class Bug:
    def __init__(self, timestep=0.1, x=3, isWrapOn=False):
        self.timestep = float(timestep)
        self.x = int(x)                 # LED index 0..7
        self.isWrapOn = bool(isWrapOn)

        # Use the SAME pins as the class example: data=23, latch=24, clock=25
        self.__shifter = Shifter(dataPin=23, latchPin=24, clockPin=25)

        self._running = False
        self._next_step_at = time.time()
        self._show()

    def _show(self):
        # light only the current LED (one-hot)
        self.__shifter.shiftByte(1 << self.x)

    def _step_once(self):
        step = random.choice([-1, 1])      # random walk
        nx = self.x + step

        if self.isWrapOn:
            self.x = nx % 8
        else:
            if 0 <= nx <= 7:
                self.x = nx

        self._show()

    def start(self):
        self._running = True
        self._next_step_at = time.time() + self.timestep

    def stop(self):
        self._running = False
        self.__shifter.clear()             # turn off LEDs when stopped

    def update(self):
        if not self._running:
            return
        now = time.time()
        if now >= self._next_step_at:
            self._step_once()
            self._next_step_at = now + self.timestep


# ------------------ main (switch logic) ------------------

if __name__ == "__main__":
    # Switches (active HIGH with pulldown): keep same as you used before
    s1, s2, s3 = 5, 6, 13

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    for s in (s1, s2, s3):
        GPIO.setup(s, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    bug = Bug(timestep=0.1, x=3, isWrapOn=False)

    # simple edge-detect on switches
    prev_s1 = GPIO.input(s1)
    prev_s2 = GPIO.input(s2)
    prev_s3 = GPIO.input(s3)

    print("Lab 6 running. s1=ON/OFF, s2=wrap toggle, s3=3x speed. CTRL+C to exit.")

    try:
        while True:
            cur_s1 = GPIO.input(s1)
            cur_s2 = GPIO.input(s2)
            cur_s3 = GPIO.input(s3)

            # s1: ON -> start, OFF -> stop
            if cur_s1 and not prev_s1:
                bug.start()
            elif (not cur_s1) and prev_s1:
                bug.stop()

            # s2: any change -> toggle wrap
            if cur_s2 != prev_s2:
                bug.isWrapOn = not bug.isWrapOn
                print("wrap =", bug.isWrapOn)
                time.sleep(0.15)   # crude debounce

            # s3: any change -> 3x speed (timestep /= 3)
            if cur_s3 != prev_s3:
                bug.timestep = max(0.01, bug.timestep / 3.0)
                print("timestep =", bug.timestep)
                time.sleep(0.15)

            prev_s1, prev_s2, prev_s3 = cur_s1, cur_s2, cur_s3

            bug.update()
            time.sleep(0.005)     # CPU breather (not a motion delay)

    except KeyboardInterrupt:
        print("\nExiting. Cleaning up GPIO...")
    finally:
        bug.stop()
        GPIO.cleanup()
