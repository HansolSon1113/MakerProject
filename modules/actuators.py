import RPi.GPIO as GPIO
import time
import threading

class DifferentialDrive:
    def __init__(self):
        self.L_PINS = [17, 27, 22, 4]
        self.R_PINS = [12, 16, 20, 21]
        
        self.L_DIR = -1
        self.R_DIR = 1
        
        self.step_delay = 0.003 

        self.seq = [
            [1,0,0,0], [1,1,0,0], [0,1,0,0], [0,1,1,0],
            [0,0,1,0], [0,0,1,1], [0,0,0,1], [1,0,0,1]
        ]

        GPIO.setmode(GPIO.BCM)
        for pin in self.L_PINS + self.R_PINS:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)

        self.current_action = "stop"
        self.running = True
        self.thread = threading.Thread(target=self._motor_loop, daemon=True)
        self.thread.start()

    def _step_one(self, pins, direction_val, step_index):
        seq_idx = step_index % 8
        if direction_val == -1:
            seq_idx = 7 - seq_idx
            
        val = self.seq[seq_idx]
        for i in range(4):
            GPIO.output(pins[i], val[i])

    def _motor_loop(self):
        step_counter = 0
        
        while self.running:
            if self.current_action == "stop":
                time.sleep(0.1)
                continue

            if self.current_action == "forward":
                self._step_one(self.L_PINS, 1 * self.L_DIR, step_counter)
                self._step_one(self.R_PINS, 1 * self.R_DIR, step_counter)
                
            elif self.current_action == "left":
                self._step_one(self.L_PINS, -1 * self.L_DIR, step_counter)
                self._step_one(self.R_PINS, 1 * self.R_DIR, step_counter)
                
            elif self.current_action == "right":
                self._step_one(self.L_PINS, 1 * self.L_DIR, step_counter)
                self._step_one(self.R_PINS, -1 * self.R_DIR, step_counter)

            step_counter += 1
            time.sleep(self.step_delay)

    def move(self, direction="stop"):
        self.current_action = direction

    def stop(self):
        self.current_action = "stop"
        time.sleep(self.step_delay * 2) 
        for pin in self.L_PINS + self.R_PINS:
            GPIO.output(pin, 0)

    def cleanup(self):
        self.running = False
        self.stop()
        if self.thread.is_alive():
            self.thread.join()


class ServoMotor:
    def __init__(self, pin, init_angle=90):
        self.pin = pin
        self.current_angle = init_angle
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        
        self.pwm = GPIO.PWM(self.pin, 50) # 50Hz
        self.pwm.start(0)
        self.set_angle(init_angle, instant=True)

    def _angle_to_duty(self, angle):
        return 2.5 + (angle / 18.0)

    def set_angle(self, target_angle, speed=0.0, instant=False):
        if instant:
            self._write_angle(target_angle)
            return

        if int(self.current_angle) == int(target_angle):
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