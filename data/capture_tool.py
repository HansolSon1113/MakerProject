import cv2
import os
import time
import subprocess
import numpy as np

base_dir = "dataset"
labels = ["left", "center", "right", "none"]
for label in labels:
    os.makedirs(os.path.join(base_dir, label), exist_ok=True)

cmd = [
    "rpicam-vid",
    "-t", "0",
    "--inline",
    "--width", "320",
    "--height", "240",
    "--codec", "mjpeg",
    "--nopreview",
    "-o", "-"
]

print("[L] Left | [C] Center | [R] Right | [N] None | [Q] Quit")

process = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10**8)

byte_buffer = b""

try:
    while True:
        chunk = process.stdout.read(4096)
        if not chunk:
            break
        byte_buffer += chunk

        a = byte_buffer.find(b'\xff\xd8')
        b = byte_buffer.find(b'\xff\xd9')

        if a != -1 and b != -1:
            jpg = byte_buffer[a:b+2]
            byte_buffer = byte_buffer[b+2:]

            frame = cv2.imdecode(
                np.frombuffer(jpg, dtype=np.uint8),
                cv2.IMREAD_COLOR
            )

            if frame is None:
                continue

            cv2.imshow("Capture View", frame)

            key = cv2.waitKey(1) & 0xFF

            save_label = ""
            if key == ord('l'):
                save_label = "left"
            elif key == ord('c'):
                save_label = "center"
            elif key == ord('r'):
                save_label = "right"
            elif key == ord('n'):
                save_label = "none"
            elif key == ord('q'):
                break

            if save_label:
                timestamp = int(time.time() * 1000)
                filename = f"{base_dir}/{save_label}/{save_label}_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Saved: {filename}")
                time.sleep(0.1)

except Exception as e:
    print(f"Error: {e}")

finally:
    process.terminate()
    cv2.destroyAllWindows()
