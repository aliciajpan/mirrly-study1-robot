"""
Robot gesture functions module.
Contains all gesture definitions and motor control commands.
"""

import time
import sys
import os

# Try to import motor control modules
try:
    from control_modules.head_control import HeadMotors
    from control_modules.torso_control import TorsoMotors
    MOTORS_AVAILABLE = True
except Exception as e:
    print(f"Warning: Motor control modules not available: {e}")
    print("Running in SIMULATION MODE (no hardware required)")
    MOTORS_AVAILABLE = False
    HeadMotors = None
    TorsoMotors = None

# Try to import media playback module
try:
    from media_player import media_player
    MEDIA_AVAILABLE = media_player.is_available()
    if MEDIA_AVAILABLE:
        print("✓ Media playback available")
except Exception as e:
    print(f"Warning: Media playback not available: {e}")
    MEDIA_AVAILABLE = False
    media_player = None

# Initialize motor controllers if available
head_motors = None
torso_motors = None

if MOTORS_AVAILABLE:
    try:
        head_motors = HeadMotors()
        torso_motors = TorsoMotors()
        print("✓ Motors initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize motors: {e}")
        print("Running in SIMULATION MODE (no hardware required)")
        MOTORS_AVAILABLE = False
        head_motors = None
        torso_motors = None

# Motor calibration limits (device-specific)
LIMITS = {
    "head_yaw":   {"left": 0, "center": 200, "right": 400},
    "head_pitch": {"up": 240, "center": 180, "down": 118},
    "eye_self":   {"left": 160, "center": 210, "right": 268},
    "eye_brow_l": {"open": 370, "close": 210},
    "eye_brow_r": {"open": 343, "close": 510},
    "arm_r": {"up": 90, "rest": 120, "down": 170}, # rest means T-pose
    "arm_l": {"up": 160, "rest": 130, "down": 80}, # rest means T-pose
    "r_shoulder": {"up": 160, "front": 70}, # up means screw face of shoulder to ceiling
    "l_shoulder": {"up": 60, "front": 150}, # up means screw face of shoulder to ceiling
}

# Speed constants
PITCH_SPEED = 1000      # Head pitch requires higher speed to overcome weight
EYELID_SPEED = 800      # Eyelids need 700-1000 speed for unlubricated mechanism


class GestureController:
    """Manages all robot gestures and coordinated movements."""

    def center_all(self):
        """Reset all motors to center positions."""
        print("CENTRE ALL")
        
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Moving to center position")
            time.sleep(2.0)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["center"], 400)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["center"], 400)
        head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["open"], EYELID_SPEED)
        head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["open"], EYELID_SPEED)

        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["down"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["down"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["front"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["front"], 0.01)

        time.sleep(2.0)

    def look_point_left(self):
        """Look and point to the left."""
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Looking and pointing left")
            time.sleep(2)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["left"], 500)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["left"], 500)
        head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["open"], EYELID_SPEED)
        head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["open"], EYELID_SPEED)

        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["up"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["up"], 0.01)
        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["down"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["front"], 0.01)

        time.sleep(2)

    def look_point_right(self):
        """Look and point to the right."""
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Looking and pointing right")
            time.sleep(2)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["right"], 500)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["right"], 500)
        head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["open"], EYELID_SPEED)
        head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["open"], EYELID_SPEED)

        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["up"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["up"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["down"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["front"], 0.01)

        time.sleep(2)

    def celebrate_arms_up(self):
        """Celebrate with arms raised."""
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Celebrating with arms up")
            time.sleep(2)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["center"], 400)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["up"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["center"], 500)
        head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["open"], EYELID_SPEED)
        head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["open"], EYELID_SPEED)

        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["up"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["up"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["up"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["up"], 0.01)

        time.sleep(2)

    def sad_look_down(self):
        """Express sadness by looking down."""
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Looking down sad")
            time.sleep(2)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["center"], 400)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["down"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["center"], 500)
        head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["close"], EYELID_SPEED)
        head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["close"], EYELID_SPEED)

        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["down"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["front"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["down"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["front"], 0.01)

        time.sleep(2)

    def talking_left_arm(self):
        """Talk while gesturing with left arm."""
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Talking with left arm gesture")
            time.sleep(2)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["center"], 400)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["center"], 500)
        head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["open"], EYELID_SPEED)
        head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["open"], EYELID_SPEED)

        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["down"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["front"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["down"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["up"], 0.01)

        time.sleep(2)

    def talking_right_arm(self):
        """Talk while gesturing with right arm."""
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Talking with right arm gesture")
            time.sleep(2)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["center"], 400)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["center"], 500)
        head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["open"], EYELID_SPEED)
        head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["open"], EYELID_SPEED)

        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["down"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["up"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["down"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["front"], 0.01)

        time.sleep(2)

    def eyes_left(self):
        """Look at left with eyes only."""
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Eyes looking left")
            time.sleep(2)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["center"], 400)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["left"], 500)
        head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["open"], EYELID_SPEED)
        head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["open"], EYELID_SPEED)

        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["down"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["front"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["down"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["front"], 0.01)

        time.sleep(2)

    def eyes_right(self):
        """Look at right with eyes only."""
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Eyes looking right")
            time.sleep(2)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["center"], 400)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["right"], 500)
        head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["open"], EYELID_SPEED)
        head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["open"], EYELID_SPEED)

        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["down"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["front"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["down"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["front"], 0.01)

        time.sleep(2)

    def gesture_with_video(self, video_path=None):
        """
        Example gesture with synchronized video playback.
        Play video on screen while performing gesture.
        
        Args:
            video_path (str): Path to video file. If None, uses default or skips video.
        """
        print("GESTURE WITH VIDEO")
        
        # Start video playback in background (non-blocking)
        video_thread = None
        if MEDIA_AVAILABLE and video_path and media_player:
            print(f"  Playing video: {video_path}")
            video_thread = media_player.play_video(
                video_path=video_path,
                fullscreen=True,
                muted=False,
                blocking=False  # Don't wait for video to finish
            )
        elif video_path:
            print(f"  [SIMULATION] Would play video: {video_path}")
        
        # Perform gesture movements
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Performing gesture with video")
            time.sleep(3.0)  # Simulate gesture duration
        else:
            # Example: Celebratory gesture
            head_motors.move("head_yaw", LIMITS["head_yaw"]["center"], 400)
            head_motors.move("head_pitch", LIMITS["head_pitch"]["up"], PITCH_SPEED)
            head_motors.move("eye_self", LIMITS["eye_self"]["center"], 500)
            head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["open"], EYELID_SPEED)
            head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["open"], EYELID_SPEED)

            torso_motors.arm_move("arm_r", LIMITS["arm_r"]["up"], 0.01)
            torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["up"], 0.01)
            torso_motors.arm_move("arm_l", LIMITS["arm_l"]["up"], 0.01)
            torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["up"], 0.01)
            
            time.sleep(0.5)
        
        # Wait for video to finish if it was started
        if video_thread:
            print("  Waiting for video to complete...")
            video_thread.join()
        
        print("  Gesture with video complete")

    def countdown_gesture(self):
        """
        Play countdown video with synchronized celebratory gesture.
        Uses: static/media/video/countdown_video.mp4
        """
        print("COUNTDOWN GESTURE")
        
        video_path = "static/media/video/countdown_video.mp4"
        
        # Start countdown video (non-blocking)
        video_thread = None
        if MEDIA_AVAILABLE and media_player:
            print(f"  Playing countdown video: {video_path}")
            video_thread = media_player.play_video(
                video_path=video_path,
                fullscreen=True,
                muted=False,
                blocking=False
            )
        else:
            print(f"  [SIMULATION] Would play countdown video: {video_path}")
        
        # Perform celebratory movements during countdown
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Performing countdown gesture")
            time.sleep(5.0)
        else:
            # Center position at start
            head_motors.move("head_yaw", LIMITS["head_yaw"]["center"], 400)
            head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], PITCH_SPEED)
            head_motors.move("eye_self", LIMITS["eye_self"]["center"], 500)
            head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["open"], EYELID_SPEED)
            head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["open"], EYELID_SPEED)
            
            # Anticipatory arm movements
            torso_motors.arm_move("arm_r", LIMITS["arm_r"]["up"], 0.01)
            torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["up"], 0.01)
            torso_motors.arm_move("arm_l", LIMITS["arm_l"]["up"], 0.01)
            torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["up"], 0.01)
            
            time.sleep(0.5)
        
        # Wait for countdown video to finish
        if video_thread:
            print("  Waiting for countdown to complete...")
            video_thread.join()
        
        print("  Countdown gesture complete")

    def show_diamond(self, duration=3.0):
        """
        Display diamond image on screen.
        Uses: static/media/image/diamond.jpeg
        
        Args:
            duration (float): How long to display the image (default: 3 seconds)
        """
        print(f"SHOW DIAMOND (duration: {duration}s)")
        
        image_path = "static/media/image/diamond.jpeg"
        
        # Display diamond image
        if MEDIA_AVAILABLE and media_player:
            print(f"  Displaying diamond: {image_path}")
            media_player.play_image(
                image_path=image_path,
                duration=duration,
                fullscreen=True,
                blocking=True
            )
        else:
            print(f"  [SIMULATION] Would display diamond: {image_path} for {duration}s")
            time.sleep(duration)
        
        print("  Diamond display complete")

    def show_star(self, duration=3.0):
        """
        Display star image on screen.
        Uses: static/media/image/star.jpeg
        
        Args:
            duration (float): How long to display the image (default: 3 seconds)
        """
        print(f"SHOW STAR (duration: {duration}s)")
        
        image_path = "static/media/image/star.jpeg"
        
        # Display star image
        if MEDIA_AVAILABLE and media_player:
            print(f"  Displaying star: {image_path}")
            media_player.play_image(
                image_path=image_path,
                duration=duration,
                fullscreen=True,
                blocking=True
            )
        else:
            print(f"  [SIMULATION] Would display star: {image_path} for {duration}s")
            time.sleep(duration)
        
        print("  Star display complete")

    def cleanup(self):
        """Release all motors and close connections."""
        print("Cleaning up motors...")
        
        # Stop any playing videos
        if MEDIA_AVAILABLE and media_player:
            media_player.stop_all()
        
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] No motors to cleanup")
            return
        
        try:
            torso_motors.release_motors()
            torso_motors.release_hands('all')
            head_motors.close()
            print("Cleanup complete.")
        except Exception as e:
            print(f"Error during cleanup: {e}")


# Create global instance
try:
    gesture_controller = GestureController()
except Exception as e:
    print(f"Error creating gesture controller: {e}")
    print("Robot server will still start but gestures may fail")
    gesture_controller = GestureController()  # Try again - this should work in simulation mode

# Gesture registry - maps gesture names to methods
GESTURES = {
    'center_all': gesture_controller.center_all,
    'look_point_left': gesture_controller.look_point_left,
    'look_point_right': gesture_controller.look_point_right,
    'celebrate_arms_up': gesture_controller.celebrate_arms_up,
    'sad_look_down': gesture_controller.sad_look_down,
    'talking_left_arm': gesture_controller.talking_left_arm,
    'talking_right_arm': gesture_controller.talking_right_arm,
    'eyes_left': gesture_controller.eyes_left,
    'eyes_right': gesture_controller.eyes_right,
    'gesture_with_video': gesture_controller.gesture_with_video,
    'countdown_gesture': gesture_controller.countdown_gesture,
    'show_diamond': gesture_controller.show_diamond,
    'show_star': gesture_controller.show_star,
}


def execute_gesture(gesture_name, **kwargs):
    """
    Execute a gesture by name with optional parameters.
    
    Args:
        gesture_name (str): Name of the gesture to execute
        **kwargs: Optional parameters to pass to the gesture (e.g., video_path)
        
    Returns:
        dict: Response with status and message
    """
    if gesture_name not in GESTURES:
        return {
            'status': 'error',
            'message': f'Gesture "{gesture_name}" not found. Available gestures: {list(GESTURES.keys())}'
        }
    
    try:
        # Call gesture with or without parameters
        gesture_func = GESTURES[gesture_name]
        if kwargs:
            gesture_func(**kwargs)
        else:
            gesture_func()
        
        return {
            'status': 'success',
            'message': f'Gesture "{gesture_name}" executed successfully'
        }
    except TypeError as e:
        # Handle cases where gesture doesn't accept parameters
        if 'unexpected keyword argument' in str(e):
            try:
                GESTURES[gesture_name]()
                return {
                    'status': 'success',
                    'message': f'Gesture "{gesture_name}" executed successfully (parameters ignored)'
                }
            except Exception as ex:
                return {
                    'status': 'error',
                    'message': f'Error executing gesture "{gesture_name}": {str(ex)}'
                }
        return {
            'status': 'error',
            'message': f'Error executing gesture "{gesture_name}": {str(e)}'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error executing gesture "{gesture_name}": {str(e)}'
        }


def get_available_gestures():
    """Get list of available gestures."""
    return list(GESTURES.keys())
