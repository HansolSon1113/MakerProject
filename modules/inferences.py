import cv2
import numpy as np
import subprocess
import tensorflow as tf
import threading
import time

class Vision:
    def __init__(self, model_path="model/model_unquant.tflite", label_path="model/labels.txt"):
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        self.h = self.input_details[0]['shape'][1]
        self.w = self.input_details[0]['shape'][2]
        self.is_float = (self.input_details[0]['dtype'] == np.float32)
        
        self.labels = [line.strip() for line in open(label_path, 'r').readlines()]
        self.target_idx = 1
        self.threshold = 0.4

        cmd = [
            "rpicam-vid", "-t", "0", "--inline", 
            "--width", "640", "--height", "240", "--framerate", "20",
            "--codec", "mjpeg", "--nopreview", "-o", "-"
        ]
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=0)

        self.latest_frame = None
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        
        print("Camera System Initializing...")
        time.sleep(1)

    def _capture_loop(self):
        stream_buffer = b""
        while self.running:
            try:
                chunk = self.process.stdout.read(4096)
                if not chunk: break
                stream_buffer += chunk
                
                a = stream_buffer.find(b'\xff\xd8')
                b = stream_buffer.find(b'\xff\xd9')
                
                if a != -1 and b != -1:
                    jpg = stream_buffer[a:b+2]
                    stream_buffer = stream_buffer[b+2:]
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if frame is not None:
                        self.latest_frame = frame
            except Exception:
                time.sleep(0.1)

    def _inference(self, img):
        img_resized = cv2.resize(img, (self.w, self.h))
        input_data = np.expand_dims(img_resized, axis=0)
        
        if self.is_float:
            input_data = (np.float32(input_data) / 127.5) - 1.0

        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        output = self.interpreter.get_tensor(self.output_details[0]['index'])
        pred = np.squeeze(output)
        
        return pred[self.target_idx] if self.is_float else pred[self.target_idx] / 255.0

    def process_frame(self):
        if self.latest_frame is None:
            return "None", 0.0, np.zeros((240, 640, 3), np.uint8)

        frame = self.latest_frame.copy()
        h, width, _ = frame.shape
        w_step = width // 3

        regions = {
            "Left": frame[:, :w_step],
            "Center": frame[:, w_step:w_step*2],
            "Right": frame[:, w_step*2:]
        }

        scores = {k: self._inference(v) for k, v in regions.items()}
        best_dir = max(scores, key=scores.get)
        best_score = scores[best_dir]
        
        result = best_dir if best_score > self.threshold else "None"

        cv2.line(frame, (w_step, 0), (w_step, h), (255, 255, 255), 2)
        cv2.line(frame, (w_step*2, 0), (w_step*2, h), (255, 255, 255), 2)
        
        cv2.putText(frame, f"L:{scores['Left']:.2f}", (10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"C:{scores['Center']:.2f}", (w_step+10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"R:{scores['Right']:.2f}", (w_step*2+10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        if result == "Left":
            cv2.rectangle(frame, (0,0), (w_step, h), (0,255,0), 3)
        elif result == "Center":
            cv2.rectangle(frame, (w_step,0), (w_step*2, h), (0,255,0), 3)
        elif result == "Right":
            cv2.rectangle(frame, (w_step*2,0), (width, h), (0,255,0), 3)
        
        return result, best_score, frame, scores

    def close(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join()

        if self.process:
            self.process.terminate()

        self.interpreter = None