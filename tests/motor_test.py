import RPi.GPIO as GPIO
import time
import smbus

L_MOTOR_PINS = [17, 27, 22, 4] 

R_MOTOR_PINS = [12, 16, 20, 21]

TRIG1, ECHO1 = 23, 24
TRIG2, ECHO2 = 5, 6
SERVO_PIN = 18
PIR_PIN = 25
BTN_PIN = 26
BUZZER_PIN = 13
LED_PIN = 19
I2C_ADDR = 0x27

bus = smbus.SMBus(1)

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    for pin in L_MOTOR_PINS + R_MOTOR_PINS:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, 0)
        
    GPIO.setup(TRIG1, GPIO.OUT)
    GPIO.setup(TRIG2, GPIO.OUT)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    
    GPIO.setup(LED_PIN, GPIO.OUT)
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    
    GPIO.setup(ECHO1, GPIO.IN)
    GPIO.setup(ECHO2, GPIO.IN)
    GPIO.setup(PIR_PIN, GPIO.IN)
    GPIO.setup(BTN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    lcd_init()
    print("Test Init")

def lcd_byte(bits, mode):
    bits_high = mode | (bits & 0xF0) | 0x08
    bits_low = mode | ((bits << 4) & 0xF0) | 0x08
    try:
        bus.write_byte(I2C_ADDR, bits_high)
        lcd_toggle_enable(bits_high)
        bus.write_byte(I2C_ADDR, bits_low)
        lcd_toggle_enable(bits_low)
    except:
        pass

def lcd_toggle_enable(bits):
    time.sleep(0.0005)
    bus.write_byte(I2C_ADDR, (bits | 0x04))
    time.sleep(0.0005)
    bus.write_byte(I2C_ADDR, (bits & ~0x04))
    time.sleep(0.0005)

def lcd_init():
    try:
        lcd_byte(0x33, 0)
        lcd_byte(0x32, 0)
        lcd_byte(0x06, 0)
        lcd_byte(0x0C, 0)
        lcd_byte(0x28, 0)
        lcd_byte(0x01, 0)
        time.sleep(0.05)
    except:
        print("LCD FAIL")

def lcd_text(message, line):
    message = message.ljust(16, " ")
    lcd_byte(0x80 if line == 1 else 0xC0, 0)
    for i in range(16):
        lcd_byte(ord(message[i]), 1)

def beep(duration=0.1):
    pwm = GPIO.PWM(BUZZER_PIN, 2000) 
    pwm.start(50)
    time.sleep(duration)
    pwm.stop()

def move_motor(pins, direction=1):
    seq = [
        [1,0,0,0], [1,1,0,0], [0,1,0,0], [0,1,1,0],
        [0,0,1,0], [0,0,1,1], [0,0,0,1], [1,0,0,1]
    ]
    if direction == -1: seq.reverse()

    for _ in range(128): 
        for step in seq:
            for i in range(4):
                GPIO.output(pins[i], step[i])
            time.sleep(0.002) 

def get_distance(trig, echo):
    GPIO.output(trig, True)
    time.sleep(0.00001)
    GPIO.output(trig, False)
    start, stop = time.time(), time.time()
    
    timeout = time.time() + 0.1
    while GPIO.input(echo) == 0:
        start = time.time()
        if start > timeout: return 0
        
    while GPIO.input(echo) == 1:
        stop = time.time()
        if stop > timeout: return 0
        
    return (stop - start) * 17150

try:
    setup()
    
    while True:
        d1 = get_distance(TRIG1, ECHO1)
        btn = GPIO.input(BTN_PIN)
        
        status = f"Dist:{d1:.0f}cm | BTN:{'Push' if btn==0 else 'Open'}"
        print(status)
        lcd_text(f"D:{d1:.0f}cm", 1)
        
        if btn == 0:
            lcd_text("Run Motors", 2)
            beep(0.2) 
            move_motor(L_MOTOR_PINS, -1)
            move_motor(R_MOTOR_PINS, -1)
            lcd_text("Done.", 2)
            
        else:
            lcd_text("Press Btn", 2)
            
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Exit.")
    GPIO.cleanup()
