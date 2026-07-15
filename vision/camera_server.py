#!/usr/bin/env python3
import sys
import os
from flask import Flask, Response

# care folder pathing
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vision.eye_camera import EyeCameraManager

def run_server():
    app = Flask(__name__)
    eye_manager = EyeCameraManager(left_index=0, right_index=1)

    @app.route('/video_feed/left')
    def video_feed_left():
        return Response(eye_manager.generate_frames("left"),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/video_feed/right')
    def video_feed_right():
        return Response(eye_manager.generate_frames("right"),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    print("Starting Camera Server on port 5001...")
    app.run(debug=False, host='0.0.0.0', port=5002, use_reloader=False)

if __name__ == '__main__':
    run_server()