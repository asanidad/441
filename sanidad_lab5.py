import RPi.GPIO as GPIO
import time
import math

led_pins = 5, 6, 13, 19, 26, 16, 20, 21, 12, 7, 8, 25
button_pin = 17 #jumper wire
PWM_base = 500
wave_f = 0.2
PHI = math.pi / 11.0

GPiO.setwarnings(False)
GPiO.setmode(GPiO.BCM)

pwms = []

for pin in led_pins:
	GPiO.setup(pin, GPiO.OUT)
	p = GPiO.PWM(pin, PWM_base)
	p.start(0)
	pwms.append(p)

GPiO.setup(button_pin, GPiO.IN, pull_up_down=GPiO.PUD_DOWN)

direction = 1
def toggle_direction(channel):
	global direction
	direction *= -1
	print("Direction:", "forward" if direction == 1 else "reverse")

GPiO.add_event_detect(BUTTON_PIN, GPiO.RISING, callbacks=toggle_direciton, bouncetime = 300)

try:
	while True:
		t = time.time()
		base = 2.0 * math.pi * wave_f + t
		for i, p in enumerate(pwms):
			s = math.sin(base - direction * i * PHI)
			B = s * s
			duty = max(0.0, min(100.0, B * 100.0))
			p.ChangeDutyCycle(duty)

except KeyboardInterrupt:
	print("\nExisting (Ctryl+C pressed). Cleaning up GPiO...:")

finally:
	for p in pwms:
		p.stop()
	GPiO.cleanup()