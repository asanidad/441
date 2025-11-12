## lab8.py — ENME441 Lab 8: run the exact sequence from the prompt

import time
from stepper_class_shiftregister_multiprocessing import Shifter, Stepper

# 74HC595 pins (BCM)
DATA_PIN  = 16
LATCH_PIN = 20
CLOCK_PIN = 21

def main():
    sh = Shifter(DATA_PIN, LATCH_PIN, CLOCK_PIN)

    # Motor 1 uses low nibble (Q0..Q3), Motor 2 uses high nibble (Q4..Q7)
    m1 = Stepper(sh, nibble='low',  mode='full', step_angle_deg=1.8, step_delay_s=0.003)
    m2 = Stepper(sh, nibble='high', mode='full', step_angle_deg=1.8, step_delay_s=0.003)

    print("Running demo…  Press CTRL+C to stop.")

    # ---------- EXACT SEQUENCE FROM THE PROMPT ----------
    m1.zero()
    m2.zero()

    m1.goAngle(90)
    m1.goAngle(-45)

    m2.goAngle(-90)
    m2.goAngle(45)

    m1.goAngle(-135)
    m1.goAngle(135)
    m1.goAngle(0)
    # ----------------------------------------------------

    print("Done.")
    time.sleep(0.2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting.")
