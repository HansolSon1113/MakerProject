import RPi.GPIO as GPIO
import time

class DifferentialDrive:
    def __init__(self):
        self.L_PINS = [17, 27, 22, 4]
        self.R_PINS = [12, 16, 20, 21]
        self.L_DIR = -1
        self.R_DIR = 1
        
        self.seq = [
            [1,0,0,0], [1,1,0,0], [0,1,0,0], [0,1,1,0],
            [0,0,1,0], [0,0,1,1], [0,0,0,1], [1,0,0,1]
        ]
        
        GPIO.setmode(GPIO.BCM)
        for pin in self.L_PINS + self.R_PINS:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)

    def _step(self, pins, direction, steps):
        sequence = self.seq[:]
        if direction == -1:
            sequence.reverse()
            
        for _ in range(steps):
            for step_val in sequence:
                for i in range(4):
                    GPIO.output(pins[i], step_val[i])
                time.sleep(0.001)

    def move(self, direction="stop"):
        if direction == "forward":
            self._step(self.L_PINS, 1 * self.L_DIR, 15)
            self._step(self.R_PINS, 1 * self.R_DIR, 15)
        elif direction == "left":
            self._step(self.L_PINS, -1 * self.L_DIR, 15)
            self._step(self.R_PINS, 1 * self.R_DIR, 15)
        elif direction == "right":
            self._step(self.L_PINS, 1 * self.L_DIR, 15)
            self._step(self.R_PINS, -1 * self.R_DIR, 15)
        else:
            self.stop()

    def stop(self):
        for pin in self.L_PINS + self.R_PINS:
            GPIO.output(pin, 0)

    def cleanup(self):
        self.stop()


class ServoMotor: 
    def __init__(self, pin, init_angle=90):
        self.pin = pin
        self.current_angle = init_angle
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        
        self.pwm = GPIO.PWM(self.pin, 50)
        self.pwm.start(0)
        self.set_angle(init_angle, instant=True)

    def _angle_to_duty(self, angle):
        return 2.5 + (angle / 18.0)

    def set_angle(self, target_angle, speed=0.0, instant=False):
        if instant:
            self._write_angle(target_angle)
            return

        if self.current_angle == target_angle:
            return

        step = 1 if target_angle > self.current_angle else -1
        
        for angle in range(int(self.current_angle), int(target_angle), step):
            duty = self._angle_to_duty(angle)
            self.pwm.ChangeDutyCycle(duty)
            time.sleep(speed)
            
        self._write_angle(target_angle)

    def _write_angle(self, angle):
        duty = self._angle_to_duty(angle)
        self.pwm.ChangeDutyCycle(duty)
        time.sleep(0.3)
        self.pwm.ChangeDutyCycle(0)
        self.current_angle = angle

    def cleanup(self):
        self.pwm.stop()