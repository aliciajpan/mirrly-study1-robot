import cv2

class EyeCameraManager:
    def __init__(self, left_index=0, right_index=2): # TODO: CHECK HW IDX
        # indices (0, 1, 2) based on how USB hardware maps on robot
        self.left_index = left_index
        self.right_index = right_index

    def generate_frames(self, eye_side):
        # streams frames from cam idx, compresses, HTTP
        if eye_side == "left":
            camera_idx = self.left_index 
        else:
            camera_idx = self.right_index

        camera = cv2.VideoCapture(camera_idx)
        
        # TODO: CHECK SIZE ON DISPLAY, keep small for less latency
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        while True:
            success, frame = camera.read()
            if not success:
                break

            # jpeg quality 50%
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
            encSuccess, buffer = cv2.imencode('.jpg', frame, encode_param)
            if not encSuccess:
                continue
                
            frame_bytes = buffer.tobytes()
            
            # yield frame in format web browsers natively understand
            # yield = temp pause function and return value to caller
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        camera.release()