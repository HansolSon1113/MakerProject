import RPi.GPIO as GPIO
import time
import smbus

# --- 1. 핀 설정 (우리가 정한 핀 번호) ---
# 왼쪽 모터 (IN1, IN2, IN3, IN4)
L_MOTOR_PINS = [4, 17, 27, 22]
# 오른쪽 모터
R_MOTOR_PINS = [12, 16, 20, 21]

TRIG1, ECHO1 = 23, 24  # 초음파1 (적재량)
TRIG2, ECHO2 = 5, 6    # 초음파2 (장애물)
SERVO_PIN = 18         # 서보모터 (뚜껑)
PIR_PIN = 25           # PIR 센서
BTN_PIN = 26           # 버튼
BUZZER_PIN = 13        # 부저
LED_PIN = 19           # LED

# LCD 설정 (I2C 주소 확인 필요: 보통 0x27 또는 0x3f)
I2C_ADDR = 0x27
bus = smbus.SMBus(1)

# --- 2. 초기화 함수 ---
def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # 출력 핀 설정
    for pin in L_MOTOR_PINS + R_MOTOR_PINS:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, 0)
        
    GPIO.setup(TRIG1, GPIO.OUT)
    GPIO.setup(TRIG2, GPIO.OUT)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    GPIO.setup(LED_PIN, GPIO.OUT)
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    
    # 입력 핀 설정
    GPIO.setup(ECHO1, GPIO.IN)
    GPIO.setup(ECHO2, GPIO.IN)
    GPIO.setup(PIR_PIN, GPIO.IN)
    GPIO.setup(BTN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) # 내부 풀업 사용
    
    # LCD 초기화 (명령어 전송)
    lcd_init()
    
    print("✅ 하드웨어 초기화 완료")

# --- 3. 기능별 함수들 ---

# LCD 관련 함수 (라이브러리 없이 직접 제어)
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
        print("❌ LCD 연결 실패 (주소 확인 필요)")

def lcd_text(message, line):
    message = message.ljust(16, " ")
    lcd_byte(0x80 if line == 1 else 0xC0, 0)
    for i in range(16):
        lcd_byte(ord(message[i]), 1)

# 초음파 거리 측정
def get_distance(trig, echo):
    GPIO.output(trig, True)
    time.sleep(0.00001)
    GPIO.output(trig, False)
    
    start, stop = time.time(), time.time()
    while GPIO.input(echo) == 0: start = time.time()
    while GPIO.input(echo) == 1: stop = time.time()
    
    return (stop - start) * 17150  # cm 단위 계산

# 스텝 모터 구동 (살짝만 움직임)
def move_motor(pins):
    seq = [[1,0,0,1], [1,0,0,0], [1,1,0,0], [0,1,0,0],
           [0,1,1,0], [0,0,1,0], [0,0,1,1], [0,0,0,1]]
    for _ in range(32): # 조금만 회전
        for step in seq:
            for i in range(4):
                GPIO.output(pins[i], step[i])
            time.sleep(0.001)

# 서보 모터 동작
def move_servo(angle):
    # 소프트웨어 PWM 방식 (간단 테스트용)
    pwm = GPIO.PWM(SERVO_PIN, 50)
    pwm.start(0)
    duty = 2 + (angle / 18)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    pwm.stop()

# --- 4. 메인 테스트 루프 ---
try:
    setup()
    print("🚀 테스트 시작! (종료하려면 Ctrl+C)")
    
    while True:
        # 1. 센서 값 읽기
        dist1 = get_distance(TRIG1, ECHO1)
        dist2 = get_distance(TRIG2, ECHO2)
        pir_val = GPIO.input(PIR_PIN)
        btn_val = GPIO.input(BTN_PIN) # 0이면 눌림
        
        # 2. 콘솔 출력
        status = f"U1:{dist1:.1f}cm | U2:{dist2:.1f}cm | PIR:{pir_val} | BTN:{'PRESSED' if btn_val==0 else 'OPEN'}"
        print(status)
        
        # 3. LCD 출력
        lcd_text(f"D1:{dist1:.0f} D2:{dist2:.0f}", 1)
        lcd_text(f"PIR:{pir_val} BTN:{'ON' if btn_val==0 else 'OF'}", 2)
        
        # 4. 동작 테스트
        # LED 깜빡임 (심장박동)
        GPIO.output(LED_PIN, not GPIO.input(LED_PIN))
        
        # 버튼 누르면 -> 부저 울림 + 모터 회전 + 서보 움직임
        if btn_val == 0: 
            print("👉 버튼 눌림: 액추에이터 테스트 실행!")
            GPIO.output(BUZZER_PIN, True)
            time.sleep(0.1)
            GPIO.output(BUZZER_PIN, False)
            
            # 서보 열기/닫기
            move_servo(90) 
            time.sleep(0.2)
            move_servo(0)
            
            # 바퀴 굴리기
            move_motor(L_MOTOR_PINS)
            move_motor(R_MOTOR_PINS)

        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n테스트 종료 (GPIO 정리)")
    GPIO.cleanup()
