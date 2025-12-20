import cv2
import numpy as np
import subprocess
import tensorflow as tf

MODEL_PATH = "model_unquant.tflite"
LABEL_PATH = "labels.txt"
CONFIDENCE_THRESHOLD = 0.6
OBJECT_CLASS_INDEX = 1

try:
    interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()
except Exception as e:
    print(f"Error loading model: {e}")
    exit()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
_, model_h, model_w, _ = input_details[0]['shape']
is_floating_model = (input_details[0]['dtype'] == np.float32)

with open(LABEL_PATH, 'r') as f:
    labels = [line.strip() for line in f.readlines()]

cmd = [
    "rpicam-vid", "-t", "0", "--inline", "--width", "1280", "--height", "720",
    "--codec", "mjpeg", "--nopreview", "-o", "-"
]
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10**8)

byte_buffer = b""

def run_inference(image_slice):
    img_resized = cv2.resize(image_slice, (model_w, model_h))
    input_data = np.expand_dims(img_resized, axis=0)

    if is_floating_model:
        input_data = (np.float32(input_data) / 127.5) - 1.0

    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()

    output_data = interpreter.get_tensor(output_details[0]['index'])
    prediction = np.squeeze(output_data)

    if is_floating_model:
        score = prediction[OBJECT_CLASS_INDEX]
    else:
        score = prediction[OBJECT_CLASS_INDEX] / 255.0
    
    return score

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

            h, w, _ = frame.shape
            
            crop_h_start = 140
            crop_h_end = 720
            
            roi_frame = frame[crop_h_start:crop_h_end, :]
            roi_h, roi_w, _ = roi_frame.shape

            w_step = roi_w // 3
            img_left = roi_frame[:, :w_step]
            img_center = roi_frame[:, w_step:w_step*2]
            img_right = roi_frame[:, w_step*2:]

            score_l = run_inference(img_left)
            score_c = run_inference(img_center)
            score_r = run_inference(img_right)

            scores = {'Left': score_l, 'Center': score_c, 'Right': score_r}
            best_pos = max(scores, key=scores.get)
            best_score = scores[best_pos]

            final_decision = "None"
            if best_score > CONFIDENCE_THRESHOLD:
                final_decision = best_pos

            cv2.line(frame, (w_step, 0), (w_step, h), (255, 255, 255), 2)
            cv2.line(frame, (w_step*2, 0), (w_step*2, h), (255, 255, 255), 2)
            cv2.line(frame, (0, crop_h_start), (w, crop_h_start), (0, 0, 255), 2)

            text = f"Action: {final_decision} ({best_score*100:.1f}%)"
            color = (0, 255, 0) if final_decision != "None" else (0, 0, 255)
            
            cv2.putText(frame, f"L:{score_l:.2f} C:{score_c:.2f} R:{score_r:.2f}", 
                        (10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
            cv2.putText(frame, text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)
            
            cv2.imshow("AI Test View", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

except Exception as e:
    print(f"Error: {e}")

finally:
    process.terminate()
    cv2.destroyAllWindows()
