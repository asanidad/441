# lab8.py — ENME441 Lab 8 demo runner (exact sequence from the prompt)

import time
from stepper_class_shiftregister_multiprocessing import Shifter, Stepper

# 74HC595 pins (BCM)
DATA_PIN  = 16
LATCH_PIN = 20
CLOCK_PIN = 21

def main():
    # Shifter and two motors: low nibble = m1 (Q0..Q3), high nibble = m2 (Q4..Q7)
    sh = Shifter(DATA_PIN, LATCH_PIN, CLOCK_PIN)
    m1 = Stepper(sh, nibble='low',  mode='full')
    m2 = Stepper(sh, nibble='high', mode='full')

    print("Running demo…  Press CTRL+C to stop.")

    # ---- EXACT LINES FROM THE PROMPT ----
    m1.zero()
    m2.zero()
    m1.goAngle(90)
    m1.goAngle(-45)
    m2.goAngle(-90)
    m2.goAngle(45)
    m1.goAngle(-135)
    m1.goAngle(135)
    m1.goAngle(0)
    # -------------------------------------

    print("Done.")
    time.sleep(0.25)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting.")
