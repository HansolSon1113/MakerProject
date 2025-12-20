import RPi.GPIO as GPIO
import time

SERVO_PIN = 18

GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)

pwm = GPIO.PWM(SERVO_PIN, 50)
pwm.start(0)

def set_angle(angle):
    duty = 2.5 + (angle / 18.0)
    
    print(f"Moving to {angle} degrees...")
    GPIO.output(SERVO_PIN, True)
    pwm.ChangeDutyCycle(duty)
    time.sleep(1)

    GPIO.output(SERVO_PIN, False)
    pwm.ChangeDutyCycle(0)

try:
    set_angle(90) 

except KeyboardInterrupt:
    pass

finally:
    pwm.stop()
    GPIO.cleanup()