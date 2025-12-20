import RPi.GPIO as GPIO
import time

L_PINS = [17, 27, 22, 4]
R_PINS = [12, 16, 20, 21]

SEQ = [
    [1,0,0,0], [1,1,0,0], [0,1,0,0], [0,1,1,0],
    [0,0,1,0], [0,0,1,1], [0,0,0,1], [1,0,0,1]
]

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in L_PINS + R_PINS:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, 0)

try:
    setup()

    while True:
        for step_val in SEQ:
            for i in range(4):
                GPIO.output(L_PINS[i], step_val[i])
            for i in range(4):
                GPIO.output(R_PINS[i], step_val[i])
            time.sleep(0.001) 

except KeyboardInterrupt:
    print("Exit.")
    GPIO.cleanup()