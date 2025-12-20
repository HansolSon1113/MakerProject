import RPi.GPIO as GPIO
import smbus
import time

class LED:
    def __init__(self, pin):
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)

    def set_state(self, state):
        GPIO.output(self.pin, state)

class Buzzer:
    def __init__(self, pin):
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin, 100)
        self.pwm.start(0)
        self.NOTES = {
            'C4': 261, 'D4': 293, 'E4': 329, 'F4': 349,
            'G4': 392, 'A4': 440, 'B4': 493, 'C5': 523
        }

    def play_tone(self, frequency, duration):
        if frequency > 0:
            self.pwm.ChangeFrequency(frequency)
            self.pwm.ChangeDutyCycle(50)
        time.sleep(duration)
        self.pwm.ChangeDutyCycle(0)

    def play_note(self, note_name, duration):
        freq = self.NOTES.get(note_name, 0)
        self.play_tone(freq, duration)

    def cleanup(self):
        self.pwm.stop()
        GPIO.output(self.pin, False)

class LCD:
    def __init__(self, i2c_addr=0x27, bus=1):
        self.addr = i2c_addr
        self.bus = smbus.SMBus(bus)
        self.init_display()

    def _write_byte(self, bits, mode):
        bits_high = mode | (bits & 0xF0) | 0x08
        bits_low = mode | ((bits << 4) & 0xF0) | 0x08
        try:
            self.bus.write_byte(self.addr, bits_high)
            self._toggle(bits_high)
            self.bus.write_byte(self.addr, bits_low)
            self._toggle(bits_low)
        except: pass

    def _toggle(self, bits):
        time.sleep(0.0005)
        self.bus.write_byte(self.addr, (bits | 0x04))
        time.sleep(0.0005)
        self.bus.write_byte(self.addr, (bits & ~0x04))
        time.sleep(0.0005)

    def init_display(self):
        try:
            init_seq = [0x33, 0x32, 0x06, 0x0C, 0x28, 0x01]
            for cmd in init_seq:
                self._write_byte(cmd, 0)
            time.sleep(0.05)
        except: pass

    def write_text(self, message, line):
        message = str(message).ljust(16, " ")
        self._write_byte(0x80 if line == 1 else 0xC0, 0)
        for char in message:
            self._write_byte(ord(char), 1)

    def clear(self):
        self._write_byte(0x01, 0)