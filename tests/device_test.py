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
    bus.write_byte(I2C_ADDR, bits_high)
    lcd_toggle_enable(bits_high)
    bus.write_byte(I2C_ADDR, bits_low)
    lcd_toggle_enable(bits_low)

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

def get_distance(trig, echo):
    GPIO.output(trig, True)
    time.sleep(0.00001)
    GPIO.output(trig, False)
    
    start, stop = time.time(), time.time()
    while GPIO.input(echo) == 0: start = time.time()
    while GPIO.input(echo) == 1: stop = time.time()
    
    return (stop - start) * 17150

def move_motor(pins):
    seq = [[1,0,0,1], [1,0,0,0], [1,1,0,0], [0,1,0,0],
           [0,1,1,0], [0,0,1,0], [0,0,1,1], [0,0,0,1]]
    for _ in range(32):
        for step in seq:
            for i in range(4):
                GPIO.output(pins[i], step[i])
            time.sleep(0.001)

def move_servo(angle):
    pwm = GPIO.PWM(SERVO_PIN, 50)
    pwm.start(0)
    duty = 2 + (angle / 18)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    pwm.stop()

try:
    setup()
    
    while True:
        dist1 = get_distance(TRIG1, ECHO1)
        dist2 = get_distance(TRIG2, ECHO2)
        pir_val = GPIO.input(PIR_PIN)
        btn_val = GPIO.input(BTN_PIN)
        
        status = f"U1:{dist1:.1f}cm | U2:{dist2:.1f}cm | PIR:{pir_val} | BTN:{'PRESSED' if btn_val==0 else 'OPEN'}"
        print(status)
        
        lcd_text(f"D1:{dist1:.0f} D2:{dist2:.0f}", 1)
        lcd_text(f"PIR:{pir_val} BTN:{'ON' if btn_val==0 else 'OF'}", 2)
        
        GPIO.output(LED_PIN, not GPIO.input(LED_PIN))

        if btn_val == 0: 
            print("Button Seqeunce Start")
            GPIO.output(BUZZER_PIN, True)
            time.sleep(0.1)
            GPIO.output(BUZZER_PIN, False)
            
            move_servo(90) 
            time.sleep(0.2)
            move_servo(0)
            
            move_motor(L_MOTOR_PINS)
            move_motor(R_MOTOR_PINS)

        time.sleep(0.5)

except KeyboardInterrupt:
    print("Exit.")
    GPIO.cleanup()
