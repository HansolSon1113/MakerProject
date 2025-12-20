import serial
import time

SERIAL_PORT = '/dev/serial0' 
BAUD_RATE = 9600

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Connected to {SERIAL_PORT} at {BAUD_RATE}")
except:
    print("Error: Could not open serial port.")
    exit()

def send_command(command):
    print(f"Sending: {command}")
    ser.write((command + "\r\n").encode())
    time.sleep(1)
    
    response = ser.read_all().decode('utf-8', errors='ignore')
    if response:
        print(f"Response: {response.strip()}")
    else:
        print("Response: (None)")

try:
    send_command("AT")
    send_command("AT+ORGL")
    send_command("AT+ROLE=0")
    send_command("AT+NAME=DoNotConnect")
    send_command("AT+PIN=0000")

except KeyboardInterrupt:
    print("Exit.")
finally:
    ser.close()