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
    "arm_r": {"up": 90, "rest": 170, "down": 170},
    "arm_l": {"up": 160, "rest": 80, "down": 80},
    "r_shoulder": {"up": 160, "rest": 70, "down": 70},
    "l_shoulder": {"up": 60, "rest": 160, "down": 160},
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

        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["rest"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["rest"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["rest"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["rest"], 0.01)

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
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["down"], 0.01)

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
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["down"], 0.01)

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
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["down"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["down"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["down"], 0.01)

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
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["down"], 0.01)
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
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["down"], 0.01)

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
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["down"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["down"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["down"], 0.01)

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
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["down"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["down"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["down"], 0.01)

        time.sleep(2)

    def cleanup(self):
        """Release all motors and close connections."""
        print("Cleaning up motors...")
        
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
}


def execute_gesture(gesture_name):
    """
    Execute a gesture by name.
    
    Args:
        gesture_name (str): Name of the gesture to execute
        
    Returns:
        dict: Response with status and message
    """
    if gesture_name not in GESTURES:
        return {
            'status': 'error',
            'message': f'Gesture "{gesture_name}" not found. Available gestures: {list(GESTURES.keys())}'
        }
    
    try:
        GESTURES[gesture_name]()
        return {
            'status': 'success',
            'message': f'Gesture "{gesture_name}" executed successfully'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error executing gesture "{gesture_name}": {str(e)}'
        }


def get_available_gestures():
    """Get list of available gestures."""
    return list(GESTURES.keys())
