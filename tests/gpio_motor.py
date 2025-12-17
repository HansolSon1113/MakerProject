import RPi.GPIO as GPIO
import time
import smbus

# --- 1. 핀 설정 (배선 가이드 기준 수정됨) ---
# 왼쪽 모터 [IN1, IN2, IN3, IN4] 순서 중요!
# 아까 배선: IN1->17, IN2->27, IN3->22, IN4->4
L_MOTOR_PINS = [17, 27, 22, 4] 

# 오른쪽 모터 [IN1, IN2, IN3, IN4]
# 아까 배선: IN1->12, IN2->16, IN3->20, IN4->21
R_MOTOR_PINS = [12, 16, 20, 21]

TRIG1, ECHO1 = 23, 24
TRIG2, ECHO2 = 5, 6
SERVO_PIN = 18
PIR_PIN = 25
BTN_PIN = 26
BUZZER_PIN = 13
LED_PIN = 19
I2C_ADDR = 0x27 # LCD 주소 (안되면 0x3f로 변경)

bus = smbus.SMBus(1)

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # 모터 핀 설정
    for pin in L_MOTOR_PINS + R_MOTOR_PINS:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, 0)
        
    GPIO.setup(TRIG1, GPIO.OUT)
    GPIO.setup(TRIG2, GPIO.OUT)
    # 부저 설정을 PWM으로 변경 (수동 부저용)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    
    GPIO.setup(LED_PIN, GPIO.OUT)
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    
    GPIO.setup(ECHO1, GPIO.IN)
    GPIO.setup(ECHO2, GPIO.IN)
    GPIO.setup(PIR_PIN, GPIO.IN)
    GPIO.setup(BTN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    lcd_init()
    print("✅ 하드웨어 설정 완료 V2")

# --- LCD 함수 (그대로 유지) ---
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
        print("❌ LCD 주소 오류 (0x27 또는 0x3f 확인)")

def lcd_text(message, line):
    message = message.ljust(16, " ")
    lcd_byte(0x80 if line == 1 else 0xC0, 0)
    for i in range(16):
        lcd_byte(ord(message[i]), 1)

# --- 수동 부저 소리 내기 (PWM) ---
def beep(duration=0.1):
    # 2000Hz 주파수로 소리 발생 (삐-)
    pwm = GPIO.PWM(BUZZER_PIN, 2000) 
    pwm.start(50)  # 듀티 사이클 50% (소리 크기 중간)
    time.sleep(duration)
    pwm.stop()

# --- 스텝 모터 구동 (속도 조절됨) ---
def move_motor(pins, direction=1):
    # 28BYJ-48 표준 시퀀스 (Half-step, 8단계)
    seq = [
        [1,0,0,0], [1,1,0,0], [0,1,0,0], [0,1,1,0],
        [0,0,1,0], [0,0,1,1], [0,0,0,1], [1,0,0,1]
    ]
    if direction == -1: seq.reverse()
    
    # 512 스텝 = 1바퀴 (대략) / 여기선 테스트로 128 스텝만
    for _ in range(128): 
        for step in seq:
            for i in range(4):
                GPIO.output(pins[i], step[i])
            # 속도 조절: 너무 빠르면 진동만 함. 0.001 -> 0.002로 늦춤
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

# --- 메인 실행 ---
try:
    setup()
    print("🚀 V2 테스트 시작 (Ctrl+C로 종료)")
    
    while True:
        # 거리 측정
        d1 = get_distance(TRIG1, ECHO1)
        btn = GPIO.input(BTN_PIN)
        
        status = f"Dist:{d1:.0f}cm | BTN:{'Push' if btn==0 else 'Open'}"
        print(status)
        lcd_text(f"D:{d1:.0f}cm", 1)
        
        if btn == 0: # 버튼 눌림
            lcd_text("Run Motors!", 2)
            print("👉 버튼 눌림! 모터 & 부저 작동")
            
            # 부저 테스트
            beep(0.2) 
            
            # 모터 테스트 (공중에 띄우고 확인하세요!)
            print("  ...왼쪽 바퀴 굴러갑니다")
            move_motor(L_MOTOR_PINS, 1)
            
            print("  ...오른쪽 바퀴 굴러갑니다")
            move_motor(R_MOTOR_PINS, 1)
            
            lcd_text("Done.", 2)
            
        else:
            lcd_text("Press Btn", 2)
            
        time.sleep(0.1)

except KeyboardInterrupt:
    GPIO.cleanup()
