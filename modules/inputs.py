import RPi.GPIO as GPIO
import time

class Button:
    def __init__(self, pin):
        self.pin = pin
        self.last_state = 1
        self.last_time = 0
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def is_pressed(self):
        state = GPIO.input(self.pin)
        detected = False
        
        if self.last_state == 1 and state == 0:
            if time.time() - self.last_time > 0.3:
                detected = True
                self.last_time = time.time()
        
        self.last_state = state
        return detected

class UltrasonicSensor:
    def __init__(self, trig_pin, echo_pin):
        self.trig = trig_pin
        self.echo = echo_pin
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trig, GPIO.OUT)
        GPIO.setup(self.echo, GPIO.IN)
        GPIO.output(self.trig, False)
        time.sleep(0.1)

    def get_distance(self):
        GPIO.output(self.trig, True)
        time.sleep(0.00001)
        GPIO.output(self.trig, False)

        start_time = time.time()
        stop_time = time.time()
        timeout = start_time + 0.04

        while GPIO.input(self.echo) == 0:
            start_time = time.time()
            if start_time > timeout: return -1

        while GPIO.input(self.echo) == 1:
            stop_time = time.time()
            if stop_time > timeout: return -1

        elapsed = stop_time - start_time
        return (elapsed * 34300) / 2

class PIRSensor:
    def __init__(self, pin):
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)

    def is_active(self):
        return GPIO.input(self.pin) == 1