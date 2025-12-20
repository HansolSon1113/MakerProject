import cv2
import numpy as np
import subprocess
import time
import tensorflow as tf

Interpreter = tf.lite.Interpreter
load_delegate = tf.lite.load_delegate

MODEL_PATH = "model_edgetpu.tflite" 
LABEL_PATH = "labels.txt"         
CONFIDENCE_THRESHOLD = 0.6          

try:
    interpreter = Interpreter(
        model_path=MODEL_PATH,
        experimental_delegates=[load_delegate('libedgetpu.so.1.0')]
    )
    interpreter.allocate_tensors()
except Exception as e:
    print(f"Error loading Edge TPU: {e}")

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
_, height, width, _ = input_details[0]['shape']

with open(LABEL_PATH, 'r') as f:
    labels = [line.strip() for line in f.readlines()]

cmd = [
    "rpicam-vid", "-t", "0", "--inline", "--width", "320", "--height", "240", 
    "--codec", "mjpeg", "--nopreview", "-o", "-"
]
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10**8)

byte_buffer = b""

try:
    while True:
        chunk = process.stdout.read(4096)
        if not chunk: break
        byte_buffer += chunk

        a = byte_buffer.find(b'\xff\xd8')
        b = byte_buffer.find(b'\xff\xd9')

        if a != -1 and b != -1:
            jpg = byte_buffer[a:b+2]
            byte_buffer = byte_buffer[b+2:]

            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None: continue

            img_resized = cv2.resize(frame, (width, height))
            input_data = np.expand_dims(img_resized, axis=0)

            interpreter.set_tensor(input_details[0]['index'], input_data)
            interpreter.invoke()

            output_data = interpreter.get_tensor(output_details[0]['index'])
            prediction = np.squeeze(output_data)
            
            class_id = np.argmax(prediction)
            score = prediction[class_id] / 255.0
            
            result_text = f"{labels[class_id]}: {score*100:.1f}%"
            
            color = (0, 255, 0)
            if score < CONFIDENCE_THRESHOLD:
                result_text = "Uncertain"
                color = (0, 0, 255)

            cv2.putText(frame, result_text, (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            cv2.imshow("AI Test View", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

except Exception as e:
    print(f"Error: {e}")

finally:
    process.terminate()
    cv2.destroyAllWindows()
