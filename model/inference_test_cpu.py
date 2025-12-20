import cv2
import numpy as np
import subprocess
import time
import tensorflow as tf

MODEL_PATH = "model_unquant.tflite"
LABEL_PATH = "labels.txt"
CONFIDENCE_THRESHOLD = 0.6

try:
    interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()
except Exception as e:
    print(f"Error loading model: {e}")
    exit()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

_, height, width, _ = input_details[0]['shape']
is_floating_model = (input_details[0]['dtype'] == np.float32)

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

            start_time = time.time()

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            img_resized = cv2.resize(frame_rgb, (width, height))
            input_data = np.expand_dims(img_resized, axis=0)

            if is_floating_model:
                input_data = (np.float32(input_data) - 127.5) / 127.5

            interpreter.set_tensor(input_details[0]['index'], input_data)
            interpreter.invoke()

            output_data = interpreter.get_tensor(output_details[0]['index'])
            prediction = np.squeeze(output_data)

            class_id = np.argmax(prediction)
            
            if is_floating_model:
                score = prediction[class_id]
                print(f"Pred: {prediction}") 
            else:
                score = prediction[class_id] / 255.0
                print(f"Pred: {prediction}")

            fps = 1.0 / (time.time() - start_time)

            label_name = labels[class_id]
            color = (0, 255, 0)
            if score < CONFIDENCE_THRESHOLD:
                label_name = "Uncertain"
                color = (0, 0, 255)

            status_text = f"{label_name}: {score*100:.1f}%"
            fps_text = f"FPS: {fps:.1f}"

            cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            cv2.putText(frame, fps_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            cv2.imshow("Inference", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

except Exception as e:
    print(f"Error: {e}")

finally:
    process.terminate()
    cv2.destroyAllWindows()
