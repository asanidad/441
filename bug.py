# ENME 441 – Lab 6
# Bug class + main loop (random-walk LED on 8-LED bar via SN74HC595)
#
# Hardware:
#   74HC595: SER->GPIO17, SRCLK->GPIO27, RCLK->GPIO22
#   MR->3V3, OE->GND, VCC->3V3, GND->GND, Q0..Q7 -> LEDs (each through 220 Ω to GND)
# Switches (active HIGH with internal pulldown): s1=GPIO5, s2=GPIO6, s3=GPIO13
#
# What it does (per prompt):
#   - Shifter class in a separate file (shifter.py) with shiftByte() and _ping()
#   - Bug class: timestep (s), x (0..7), isWrapOn (wrap vs clamp), and a private Shifter
#   - start(): begin moving the lit pixel at current speed
#   - stop(): stop and turn off LED
#   - Main loop watches s1,s2,s3:
#       s1: on -> bug runs, off -> bug stops
#       s2: any change -> toggle wrapping
#       s3: any change -> speed up by 3x (timestep /= 3)

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

        # private shifter (composition)
        self.__shifter = Shifter(serialPin=17, clockPin=27, latchPin=22)

        # run state + timer for step scheduling
        self._running = False
        self._next_step_at = time.time()

        # show initial position
        self._show()

    def _show(self):
        # light only the current position
        self.__shifter.shiftByte(1 << self.x)

    def _step_once(self):
        # random walk: -1 or +1 with equal probability
        step = random.choice([-1, 1])
        nx = self.x + step

        if self.isWrapOn:
            self.x = nx % 8
        else:
            # clamp at edges (don’t move off the bar)
            if 0 <= nx <= 7:
                self.x = nx

        self._show()

    def start(self):
        self._running = True
        # schedule next step from now
        self._next_step_at = time.time() + self.timestep

    def stop(self):
        self._running = False
        self.__shifter.shiftByte(0)  # turn off LED when stopped

    def update(self):
        """Call this frequently from the main loop. It advances the bug
        when the timestep interval has elapsed."""
        if not self._running:
            return
        now = time.time()
        if now >= self._next_step_at:
            self._step_once()
            self._next_step_at = now + self.timestep


# ------------------ main (switch logic) ------------------

if __name__ == "__main__":
    # switches: pull-down so idle=LOW, pressed=HIGH
    s1, s2, s3 = 5, 6, 13
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    for s in (s1, s2, s3):
        GPIO.setup(s, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    bug = Bug(timestep=0.1, x=3, isWrapOn=False)

    # remember previous switch states to detect changes (simple edge detect)
    prev_s1 = GPIO.input(s1)
    prev_s2 = GPIO.input(s2)
    prev_s3 = GPIO.input(s3)

    print("Lab 6 running. s1=ON/OFF, s2=wrap toggle, s3=3x speed.")
    print("CTRL+C to exit.")

    try:
        while True:
            # read all three
            cur_s1 = GPIO.input(s1)
            cur_s2 = GPIO.input(s2)
            cur_s3 = GPIO.input(s3)

            # s1: ON -> start, OFF -> stop
            if cur_s1 and not prev_s1:
                bug.start()
            elif (not cur_s1) and prev_s1:
                bug.stop()

            # s2: on ANY change, flip wrap
            if cur_s2 != prev_s2:
                bug.isWrapOn = not bug.isWrapOn
                print("wrap =", bug.isWrapOn)
                # crude debounce
                time.sleep(0.15)

            # s3: on ANY change, 3x speed (timestep /= 3)
            if cur_s3 != prev_s3:
                bug.timestep = max(0.01, bug.timestep / 3.0)
                print("timestep =", bug.timestep)
                time.sleep(0.15)

            # remember states for next iteration
            prev_s1, prev_s2, prev_s3 = cur_s1, cur_s2, cur_s3

            # advance bug if running and time for next step
            bug.update()

            # small idle to keep CPU calm (not a movement delay)
            time.sleep(0.005)

    except KeyboardInterrupt:
        print("\nExiting. Cleaning up GPIO...")
    finally:
        bug.stop()
        GPIO.cleanup()
