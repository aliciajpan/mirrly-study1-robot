import cv2
import threading
import time

class EyeCameraManager:
    def __init__(self, left_index=0, right_index=2): # TODO: CHECK HW IDX
        # indices (0, 1, 2) based on how USB hardware maps on robot
        self.indices = {
            "left": left_index,
            "right": right_index
        }
        self.left_index = left_index
        self.right_index = right_index

        self.cameras = {}
        self.frames = {"left": None, "right": None}
        self.running = True

        for side, i in self.indices.items():
            capture = cv2.VideoCapture(i)

            # force MJPG compression to prevent USB bandwidth bottlenecks on RPi
            capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            # TODO: CHECK SIZE ON DISPLAY, keep small for less latency
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            if not capture.isOpened():
                print(f"[ERROR] Could not open {side} camera at index {i}")
            else:
                print(f"[SUCCESS] Opened {side} camera at index {i}")
                
            self.cameras[side] = capture
            
            # persistent bkgd thread for each camera
            thread = threading.Thread(target=self._update_camera, args=(side,), daemon=True)
            thread.start()

    def _update_camera(self, eye_side): # cts frames
        capture = self.cameras[eye_side]
        while self.running:
            if capture and capture.isOpened():
                success, frame = capture.read()
                if success:
                    self.frames[eye_side] = frame
                else:
                    time.sleep(0.01)
            else:
                time.sleep(0.1)

    def generate_frames(self, eye_side): # sends to browser
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50] # jpeg quality 50%

        while self.running:
            frame = self.frames.get(eye_side)
            if frame is None:
                time.sleep(0.03) # waiting for 1st frame
                continue

            encSuccess, buffer = cv2.imencode('.jpg', frame, encode_param)
            if not encSuccess:
                continue
                
            frame_bytes = buffer.tobytes()
            
            # yield frame in format web browsers natively understand
            # yield = temp pause function and return value to caller
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            # cap browser stream speed (~30 fps) to save CPU
            time.sleep(0.033)
            
    def release_cams(self):
        self.running = False
        for capture in self.cameras.values():
            if capture and capture.isOpened():
                capture.release()
