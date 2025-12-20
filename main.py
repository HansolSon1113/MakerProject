import cv2
import time
import RPi.GPIO as GPIO

from modules.actuators import DifferentialDrive, ServoMotor
from modules.inputs import Button, UltrasonicSensor, PIRSensor
from modules.outputs import LED, Buzzer, LCD
from modules.services import Bluetooth
from modules.inferences import Vision

def main():
    print("Initializing Autonomous Waste Bin...")

    try:
        drive_base = DifferentialDrive()
        lid_servo = ServoMotor(pin=18, init_angle=90) 

        sensor_load = UltrasonicSensor(trig_pin=23, echo_pin=24)
        sensor_obstacle = UltrasonicSensor(trig_pin=5, echo_pin=6)
        pir = PIRSensor(pin=25)
        btn_power = Button(pin=26)

        led_status = LED(pin=19)
        buzzer = Buzzer(pin=13)
        lcd = LCD(i2c_addr=0x27)
        
        bt_server = Bluetooth()
        ai_system = Vision()

        system_active = False
        print("System Ready")
        lcd.write_text("System Ready", 1)
        lcd.write_text("Waiting BT...", 2)

        while True:
            if btn_power.is_pressed():
                system_active = not system_active
                led_status.set_state(system_active)
                print(f"Manual State Change: {system_active}")

            bt_cmd = bt_server.update()
            if bt_cmd:
                print(f"BT Command: {bt_cmd}")
                if bt_cmd == '0':
                    system_active = False
                elif bt_cmd == '1':
                    system_active = True
                elif bt_cmd == '2':
                    dist = sensor_load.get_distance()
                    bt_server.send_byte(3 if 0 < dist < 3 else 4)
                
                led_status.set_state(system_active)

            dist_load = sensor_load.get_distance()
            dist_front = sensor_obstacle.get_distance()
            motion_detected = pir.is_active()
            
            direction, score, frame, scores = ai_system.process_frame()

            if 0 < dist_load < 3:
                drive_base.stop()
                buzzer.play_note('C4', 0.1); time.sleep(0.05)
                buzzer.play_note('E4', 0.1); time.sleep(0.05)
                buzzer.play_note('G4', 0.1); time.sleep(0.05)
                buzzer.play_note('C5', 0.2)
                
                print("Bin Full")
                lcd.write_text("!! BIN FULL !!", 1)
                lcd.write_text("Please Empty", 2)
                cv2.putText(frame, "BIN FULL!", (180, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 3)
                
                lid_servo.set_angle(180, speed=0.02)

            elif system_active and motion_detected and (0 < dist_front < 20):
                drive_base.stop()
                print(f"Opening Lid (Dist: {dist_front:.1f}cm)")
                
                lcd.write_text("Motion Detect", 1)
                lcd.write_text("Opening...", 2)
                
                lid_servo.set_angle(180, speed=0.02)
                time.sleep(5) 
                
                lcd.write_text("Closing...", 2)
                lid_servo.set_angle(90, speed=0.02)
                time.sleep(1)

            elif system_active:
                if 0 < dist_front < 10:
                    drive_base.stop()
                    lcd.write_text("Running...", 1)
                    lcd.write_text("OBSTACLE", 2)
                    cv2.putText(frame, "OBSTACLE", (200, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
                else:
                    load_msg = f"L:{dist_load:.0f}cm" if dist_load > 0 else "L:Err"
                    lcd.write_text(f"Run: {direction}", 1)
                    lcd.write_text(load_msg, 2)

                    if direction == "Center": drive_base.move("forward")
                    elif direction == "Left": drive_base.move("left")
                    elif direction == "Right": drive_base.move("right")
                    else: drive_base.stop()

            else:
                drive_base.stop()
                lcd.write_text("Standby Mode", 1)
                lcd.write_text("BT Ready", 2)

            cv2.imshow("Split Detection View", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("Stopping...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'lid_servo' in locals(): lid_servo.cleanup()
        if 'drive_base' in locals(): drive_base.cleanup()
        if 'lcd' in locals(): lcd.clear()
        if 'bt_server' in locals(): bt_server.cleanup()
        if 'ai_system' in locals(): ai_system.close()
        GPIO.cleanup()
        cv2.destroyAllWindows()
        print("Terminated")

if __name__ == "__main__":
    main()