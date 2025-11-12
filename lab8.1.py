# lab8.py
# ENME441 – Lab 8 demo runner for two steppers via 74HC595

import time
from stepper_class_shiftregister_multiprocessing import (
    Shifter, Stepper, STEP_DELAY
)

# 74HC595 pins (BCM) — these match what you’ve been using
DATA_PIN  = 16
LATCH_PIN = 20
CLOCK_PIN = 21

# --------------------------------------
# Helper: step *both* motors together
# --------------------------------------
def step_together(sh, m1, m2, steps1, steps2):
    """
    Step two motors simultaneously with ONE commit per loop.
    Positive steps => forward, negative => reverse.
    """
    d1 = 1 if steps1 >= 0 else -1
    d2 = 1 if steps2 >= 0 else -1
    r1 = abs(steps1)
    r2 = abs(steps2)

    # reset ramp counters for a clean start
    m1._step_count = 0
    m2._step_count = 0

    while r1 > 0 or r2 > 0:
        if r1 > 0:
            m1.prepare_step(d1)
            r1 -= 1
        else:
            m1.prepare_hold()

        if r2 > 0:
            m2.prepare_step(d2)
            r2 -= 1
        else:
            m2.prepare_hold()

        # one write for both motors
        sh.commit()

        # simple shared delay; both use same timing profile
        time.sleep(STEP_DELAY)

# --------------------------------------
# Angle helpers using shortest path math
# --------------------------------------
def angle_to_steps(motor, target_deg):
    # (-180, 180] delta
    delta = (target_deg - motor.angle) % 360.0
    if delta > 180.0:
        delta -= 360.0
    steps = int(round(delta * motor.steps_per_rev / 360.0))
    return steps, delta

def go_both_angles(sh, m1, a1, m2, a2):
    s1, d1 = angle_to_steps(m1, a1)
    s2, d2 = angle_to_steps(m2, a2)
    step_together(sh, m1, m2, s1, s2)
    m1.angle = (m1.angle + d1) % 360.0
    m2.angle = (m2.angle + d2) % 360.0


# --------------------------------------
# Demo sequence (matches the lab)
# --------------------------------------
def main():
    sh = Shifter(DATA_PIN, LATCH_PIN, CLOCK_PIN)
    m1 = Stepper(sh, nibble='low',  mode='full')   # Q0..Q3
    m2 = Stepper(sh, nibble='high', mode='full')   # Q4..Q7

    print("Running demo…  Press CTRL+C to stop.")

    # 1) zero both
    m1.zero(); m2.zero()
    time.sleep(0.2)

    # 2) Your lab requires simultaneous operation.
    #    We issue moves in *pairs* so both travel together.

    # m1.goAngle(90) and m1.goAngle(-45) (paired with a 'hold' on m2)
    go_both_angles(sh, m1,  90, m2, m2.angle)   # m2 holds position
    go_both_angles(sh, m1, -45, m2, m2.angle)   # m2 holds position

    # m2.goAngle(-90) and m2.goAngle(45) (paired with a 'hold' on m1)
    go_both_angles(sh, m1, m1.angle, m2, -90)   # m1 holds
    go_both_angles(sh, m1, m1.angle, m2,  45)   # m1 holds

    # m1.goAngle(-135); m1.goAngle(135); m1.goAngle(0)
    go_both_angles(sh, m1, -135, m2, m2.angle)
    go_both_angles(sh, m1,  135, m2, m2.angle)
    go_both_angles(sh, m1,    0, m2, m2.angle)

    print("Done.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting.")
