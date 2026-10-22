import time
import sys
import os
import random
import threading
import multiprocessing
import signal
from multiprocessing import Process

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
    "head_yaw":   {"left": 60, "center": 200, "right": 340},
    "head_pitch": {"up": 200, "center": 150, "down": 118},
    "eye_self":   {"left": 160, "center": 210, "right": 268},
    "eye_brow_l": {"open": 370, "close": 210},
    "eye_brow_r": {"open": 343, "close": 510},
    "arm_r": {"up": 90, "rest": 120, "down": 170}, # rest means T-pose
    "arm_l": {"up": 110, "rest": 80, "down": 30}, # rest means T-pose
    "r_shoulder": {"up": 175, "front": 80}, # up means screw face of shoulder to ceiling
    "l_shoulder": {"up": 60, "front": 160}, # up means screw face of shoulder to ceiling
}

# Speed constants
PITCH_SPEED = 800      # Head pitch requires higher speed to overcome weight
EYELID_SPEED = 800      # Eyelids need 700-1000 speed for unlubricated mechanism
BLINK_SPEED = 1000

# Concurrency primitives (imported by robot_server)
Gesture_stop = threading.Event()  # Set to pause/resume, not for hard stop
motor_lock = threading.Lock()

# Idle motion control flags
Idle_paused = threading.Event()  # Set when idle motions should pause
Idle_paused.set()  # Start paused (unpause when gesture starts)
idle_threads = []  # Track background idle threads

def interruptible_sleep(duration: float):
    """
    Sleep for duration seconds, but respond to Gesture_stop flag for pause/resume.
    
    When Gesture_stop is set, the gesture pauses and waits for it to be cleared.
    This allows for pause/resume functionality without terminating the gesture.
    
    Args:
        duration (float): How long to sleep in seconds
    """
    end_time = time.time() + duration
    while time.time() < end_time:
        # If pause flag is set, wait for it to be cleared (resume)
        if Gesture_stop.is_set():
            print("  [PAUSE] Gesture paused, waiting for resume...")
            # Wait in small increments so we can still detect clear()
            while Gesture_stop.is_set():
                time.sleep(0.05)  # Check every 50ms if pause is still active
            print("  [RESUME] Gesture resumed")
        
        # Sleep in small chunks (0.1s) to check stop flag frequently
        remaining = end_time - time.time()
        if remaining <= 0:
            break
        time.sleep(min(0.1, remaining))


# Background idle motion functions
def idle_eyebrow_motion():
    """
    Background thread: Continuous idle eyebrow blinking.
    Runs in parallel with gestures, respects pause flag.
    """
    while True:
        try:
            Idle_paused.wait()  # Block when paused
            probability = 0.07  # Probability of eyebrow idle movement per cycle
            blink_speed = random.choice([800, 1000])
            
            if random.random() < probability:
                if not MOTORS_AVAILABLE:
                    print("  [SIMULATION] Idle eyebrow blink")
                else:
                    try:
                        head_motors.move("eye_brow_l", "close", blink_speed - 100)
                        time.sleep(0.01)
                        head_motors.move("eye_brow_r", "close", blink_speed)
                        sleep_dur = 0.4 if blink_speed == 1000 else 0.8 if blink_speed == 800 else 0.9
                        time.sleep(sleep_dur)
                        head_motors.move("eye_brow_l", "open", blink_speed - 100)
                        time.sleep(0.01)
                        head_motors.move("eye_brow_r", "open", blink_speed)
                    except Exception as e:
                        # Silently continue on port errors (gesture likely terminated)
                        pass
            
            time.sleep(0.5)
        except Exception as e:
            # Catch any unexpected errors and continue
            time.sleep(0.5)


def idle_head_yaw_motion():
    """
    Background thread: Continuous idle head yaw (side-to-side) movement.
    Runs in parallel with gestures, respects pause flag.
    Higher priority than gestures to avoid override.
    """
    while True:
        try:
            Idle_paused.wait()  # Block when paused
            probability = 0.07  # Probability of head movement per cycle
            
            if random.random() < probability:
                if not MOTORS_AVAILABLE:
                    print("  [SIMULATION] Idle head yaw roll")
                else:
                    try:
                        random_value = random.randint(0, 300)
                        random_speed = random.randint(300, 500)
                        head_motors.move("head_yaw", random_value, random_speed)
                        random_rt = random.randint(1, 3)
                        time.sleep(random_rt)
                        head_motors.move("head_yaw", 180, random_speed)  # Return to center
                    except Exception as e:
                        # Silently continue on port errors (gesture likely terminated)
                        pass
            
            time.sleep(0.5)
        except Exception as e:
            # Catch any unexpected errors and continue
            time.sleep(0.5)


def start_idle_motions():
    """Start background idle motion threads."""
    global idle_threads
    
    if MOTORS_AVAILABLE:
        # In production mode, gestures run in a separate process that controls the motors.
        # Starting idle threads here would compete for the same serial port.
        print("✓ Idle motions disabled in production to avoid port conflicts")
        return
    else:
        print("✓ Idle motions ready (simulation mode)")
    
    # Resume idle motions
    Idle_paused.set()
    
    # Create and start threads if not already running
    if not idle_threads or not any(t.is_alive() for t in idle_threads):
        eyebrow_thread = threading.Thread(target=idle_eyebrow_motion, daemon=True)
        yaw_thread = threading.Thread(target=idle_head_yaw_motion, daemon=True)
        
        #eyebrow_thread.start()
        #yaw_thread.start()
        
        idle_threads = [eyebrow_thread, yaw_thread]
        print("✓ Idle motions started")
    else:
        print("✓ Idle motions resumed")


def stop_idle_motions():
    """Pause idle motions (e.g., during gesture execution)."""
    Idle_paused.clear()
    print("  Idle motions paused")


class GestureController:
    """Manages all robot gestures and coordinated movements."""

    def blinking(self, duration):
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] blinking function for {duration} sec")
            interruptible_sleep(2.0)
            return
        
        start_time = time.time()

        try:
            head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["close"], BLINK_SPEED - 100)
            time.sleep(0.01)
            head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["close"], BLINK_SPEED)
            time.sleep(0.4)
            head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["open"], BLINK_SPEED - 100)
            time.sleep(0.01)
            head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["open"], BLINK_SPEED)

        except Exception as e:
            print(f"Error in eyelid blinking movement: {e}")
            time.sleep(0.01)

        if (duration > 1):
            time.sleep(0.5)

        elapsed_time = time.time()-start_time
        # print("time to blink:", elapsed_time)
        remaining_time = max(0.01, duration-elapsed_time)
        
        # print("time to blink:", elapsed_time)
        # elapsed_time = time.time()-start_time
        interruptible_sleep(remaining_time)

    def close_eyes(self):
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Closing eyes")
            interruptible_sleep(2.0)
            return
        
        head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["close"], BLINK_SPEED - 100)
        time.sleep(0.01)
        head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["close"], BLINK_SPEED)

        interruptible_sleep(2.0)

    def open_eyes(self):
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Opening eyes")
            interruptible_sleep(2.0)
            return
        
        head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["open"], BLINK_SPEED - 100)
        time.sleep(0.01)
        head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["open"], BLINK_SPEED)

        interruptible_sleep(2.0)

    def pitch_tester(self):
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Pitch range test")
            interruptible_sleep(2.0)
            return
        
        head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], PITCH_SPEED)
        print("center")
        time.sleep(3)

        head_motors.move("head_pitch", LIMITS["head_pitch"]["up"], PITCH_SPEED)
        print("up")
        time.sleep(3)

        head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], PITCH_SPEED)
        print("center")
        time.sleep(3)

        head_motors.move("head_pitch", LIMITS["head_pitch"]["down"], PITCH_SPEED)
        print("down")
    
    def center_all(self):
        
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Moving to center position")
            interruptible_sleep(2.0)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["center"], 400)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["center"], 400)

        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["down"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["down"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["front"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["front"], 0.01)

        interruptible_sleep(2.0)

    def blink_test(self):
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] blinking")
            interruptible_sleep(2)
            return      

        blink_speed = 800
        head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["close"], blink_speed - 100)
        time.sleep(0.01)
        head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["close"], blink_speed)
        sleep_dur = 0.4 if blink_speed == 1000 else 0.8 if blink_speed == 800 else 0.9
        time.sleep(sleep_dur)
        head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["open"], blink_speed - 100)
        time.sleep(0.01)
        head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["open"], blink_speed)

        interruptible_sleep(2)

    def look_point_left(self):
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Looking and pointing left")
            interruptible_sleep(2)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["left"], 500)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["left"], 500)

        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["rest"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["up"], 0.01)
        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["down"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["front"], 0.01)

        interruptible_sleep(2)

    def look_point_right(self):
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Looking and pointing right")
            interruptible_sleep(2)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["right"], 500)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["right"], 500)

        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["rest"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["up"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["down"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["front"], 0.01)

        interruptible_sleep(2)

    def celebrate_arms_up(self):
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Celebrating with arms up")
            interruptible_sleep(2)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["center"], 400)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["up"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["center"], 500)

        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["up"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["front"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["up"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["front"], 0.01)

        interruptible_sleep(2)

    def sad_look_down(self):
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Looking down sad")
            interruptible_sleep(2)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["center"], 400)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["down"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["center"], 500)

        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["down"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["front"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["down"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["front"], 0.01)

        interruptible_sleep(2)

    def talking_left_arm(self):
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Talking with left arm gesture")
            interruptible_sleep(2)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["center"], 400)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["center"], 500)

        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["down"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["front"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["down"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["up"], 0.01)

        interruptible_sleep(2)

    def talking_right_arm(self):
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Talking with right arm gesture")
            interruptible_sleep(2)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["center"], 400)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["center"], 500)

        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["down"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["up"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["down"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["front"], 0.01)

        interruptible_sleep(2)

    def talking_both_arms(self):
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Talking with both arm gesture")
            interruptible_sleep(2)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["center"], 400)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["center"], 500)

        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["down"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["up"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["down"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["up"], 0.01)

        interruptible_sleep(2)

    def eyes_left(self):
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Eyes looking left")
            interruptible_sleep(2)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["center"], 400)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["left"], 500)

        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["down"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["front"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["down"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["front"], 0.01)

        interruptible_sleep(2)

    def eyes_right(self):
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Eyes looking right")
            interruptible_sleep(2)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["center"], 400)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["right"], 500)

        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["down"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["front"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["down"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["front"], 0.01)

        interruptible_sleep(2)

    def turn_head_left(self):
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Head turning left")
            interruptible_sleep(2)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["left"], 400)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["right"], 500)

        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["down"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["front"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["down"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["front"], 0.01)

        interruptible_sleep(2)

    def turn_head_right(self):
        if not MOTORS_AVAILABLE:
            print("  [SIMULATION] Head turning right")
            interruptible_sleep(2)
            return
        
        head_motors.move("head_yaw", LIMITS["head_yaw"]["right"], 400)
        head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], PITCH_SPEED)
        head_motors.move("eye_self", LIMITS["eye_self"]["right"], 500)

        torso_motors.arm_move("arm_r", LIMITS["arm_r"]["down"], 0.01)
        torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["front"], 0.01)
        torso_motors.arm_move("arm_l", LIMITS["arm_l"]["down"], 0.01)
        torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["front"], 0.01)

        interruptible_sleep(2)
        
    def overall_intro_tts(self):
        # self.play_sound("MirrlyOverallIntro.mp3", blocking=False)

        # it's nice to meet you
        self.open_eyes()
        self.center_all()
        self.talking_both_arms()
        self.center_all()
        self.blinking(2)
        # thank you for coming
        self.celebrate_arms_up()
        self.center_all()
        self.blinking(1)
        self.talking_left_arm()
        self.center_all()
        # during this appt
        self.blinking(2)
        self.talking_right_arm()
        self.center_all()
        self.blinking(2)
        # first, let's learn a bit about amblyopia
        self.celebrate_arms_up()
        self.center_all()

        # Buffer to guarantee audio finishes before process termination
        # interruptible_sleep(3.0)

    def video_tts_all(self): # audio is 48 sec long
            self.open_eyes()
            self.center_all()
            print('video_tts_all')
            self.video_tts_1()
            self.video_tts_2()
            self.video_tts_3()
            self.video_tts_4()
            
    def video_tts_1(self): # audio is 48 sec long
        # did you know
        self.open_eyes()
        self.center_all()
        self.talking_right_arm()
        self.center_all()
        self.blinking(2)
        # then the brain is happy
        self.talking_both_arms()
        self.center_all()
        self.blinking(2)
        # and you have to pick
        self.look_point_right()
        self.blinking(2)
        self.center_all()
        # sometimes our eyes
        self.blinking(3)
        self.blinking(2)
        self.center_all()
        # it is called
        self.talking_both_arms()
        self.center_all()
        # happen because of
        self.talking_right_arm()
        self.blinking(2)
        self.center_all()
        # drooping
        self.sad_look_down()
        self.blinking(1)
        self.center_all()

    def video_tts_2(self): # audio is 13 sec long
        self.open_eyes()
        self.center_all()
        # over time
        self.blinking(2)
        self.talking_right_arm()
        self.blinking(3)
        self.center_all()
        # it can also
        self.talking_left_arm()
        self.blinking(1)
        self.center_all()

    def video_tts_3(self): # audio is 56 sec long
        self.open_eyes()
        self.center_all()
        # harder to see depth
        self.talking_both_arms()
        self.blinking(1)
        self.center_all()
        #
        self.talking_left_arm()
        self.blinking(2)
        self.center_all()
        #
        self.blinking(1)
        self.talking_right_arm()
        self.blinking(3)
        self.center_all()
        # it's best to start...
        self.blinking(2)
        self.talking_both_arms()
        self.blinking(3)
        self.blinking(3)
        self.center_all()

        self.blinking(2)
        self.celebrate_arms_up()
        self.blinking(3)
        # your vision...
        self.center_all()
        self.talking_both_arms()
        self.blinking(4)
        self.center_all()
        self.blinking(5)
        #
        self.turn_head_left()
        self.turn_head_right()
        self.center_all()
        self.blinking(2)

    def video_tts_4(self): # audio is 21 sec long
        self.open_eyes()
        self.center_all()
        # lots of fun
        self.celebrate_arms_up()
        self.blinking(3)
        self.blinking(3)
        self.center_all()
        #
        self.talking_left_arm()
        self.center_all()
        self.talking_both_arms()
        self.blinking(2)
        self.celebrate_arms_up()
        self.blinking(2)
        self.center_all()
        time.sleep(0.5)
        self.close_eyes()
        
    def intro_game(self): # audio is 51 sec long 
        print('intro_game')
        self.open_eyes()
        self.center_all()
        self.celebrate_arms_up()
        self.blinking(1)
        self.center_all()
        #
        self.talking_both_arms()
        self.blinking(2)
        self.center_all()
        # im going to show you 
        self.talking_both_arms()
        self.blinking(2)
        self.center_all()
        #
        # TIMING ADJUSTMENT HERE
        self.look_point_right()
        self.blinking(4)
        self.center_all()
        #
        self.talking_right_arm()
        self.blinking(2)
        self.blinking(3)
        self.center_all()
        
    def game_tts_1_prompt(self): # audio is 15 sec long
        self.open_eyes()
        self.center_all()
        self.talking_both_arms()
        self.center_all()
        # In his right eye, ...
        self.blinking(1)
        self.talking_left_arm() # mirrly POV and participant POV are opposite directions
        self.center_all()
        self.blinking(1)

        # ... made his vision cloudy
        self.sad_look_down()
        self.center_all()

        # Which of Mikey's eyes...
        self.talking_both_arms()

    def game_tts_1_answer(self): # audio is 8 sec long
        self.open_eyes()
        self.center_all()
        self.show_belly_image("AnswerLSEye.png", duration=9.0)
        self.open_eyes()
        self.talking_right_arm() # right answer is LS from participant POV
        self.center_all()
        self.blinking(1)
        self.center_all()

    def game_tts_2_prompt(self): # audio is 14 sec long
        self.open_eyes()
        self.center_all()
        self.look_point_right()
        self.blinking(2)
        self.center_all()
        self.blinking(1)

        # covered part of their vision in their left eye
        self.talking_right_arm()
        self.center_all()

        time.sleep(1)
        # which of Alex's eyes...
        self.talking_both_arms()

    def game_tts_2_answer(self): # audio is 6 sec long
        self.open_eyes()
        self.center_all()
        self.show_belly_image("AnswerRSEye.png", duration=9.0)
        self.open_eyes()
        self.talking_left_arm()
        self.center_all()

    def game_tts_3_prompt(self): # audio is 15 sec long
        self.open_eyes()
        self.center_all()
        self.blinking(3)
        self.blinking(2)
        #start when Fiona used to have an
        self.talking_left_arm()
        self.blinking(1)
        self.blinking(2)
        self.center_all()
        # which eye do you think...
        self.talking_both_arms()

    def game_tts_3_answer(self): # audio is 7 sec long
        self.open_eyes()
        self.center_all()
        self.show_belly_image("AnswerLSEye.png", duration=9.0)
        self.open_eyes()
        self.talking_right_arm()
        self.blinking(2)
        self.center_all()

    def game_tts_4_prompt(self): # audio is 16 sec long
        self.open_eyes()
        self.center_all()
        self.blinking(1)
        self.look_point_right()
        self.center_all()

        # She used to get...
        self.talking_left_arm()
        self.blinking(1)
        self.center_all()

        self.talking_both_arms()
        self.blinking(2)

    def game_tts_4_answer(self): # audio is 7 sec long
        self.open_eyes()
        self.center_all()
        self.show_belly_image("AnswerLSEye.png", duration=9.0)
        self.open_eyes()
        self.talking_right_arm()
        self.blinking(2)
        self.center_all()

    def game_tts_5_prompt(self): # audio is 14 sec long
        self.open_eyes()
        self.center_all()
        self.blinking(2)
        self.look_point_right()
        self.center_all()

        self.blinking(2)
        # Daniel's vision is blurry
        self.talking_right_arm()
        self.center_all()

        self.blinking(1)
        # which eye is should
        self.talking_both_arms()

    def game_tts_5_answer(self): # audio is 6 sec long
        self.open_eyes()
        self.center_all()
        self.show_belly_image("AnswerRSEye.png", duration=9.0)
        self.open_eyes()
        self.talking_left_arm()
        self.blinking(2)
        self.center_all()

    def outro_game(self):
        print('outro_game')
        self.open_eyes()
        self.center_all()
        self.celebrate_arms_up()
        self.center_all()
        self.close_eyes()

    def sim_1_gesture(self, target_side="left", **kwargs):
        # Buffer to allow camera stream connections to settle on the USB bus
        time.sleep(0.5)

        try:
            self.open_eyes()
            self.center_all()
        except Exception as e:
            print(f"[SIM_1 HEAD WARN] {e}")

        side = str(target_side).strip().lower()

        if side in ["left", "ls"]:
            print("--> Pointing to participant LEFT eye (using Mirrly's right arm)")
            self.talking_right_arm()
        elif side in ["right", "rs"]:
            print("--> Pointing to participant RIGHT eye (using Mirrly's left arm)")
            self.talking_left_arm()

        try:
            self.blinking(1)
            self.center_all()
        except Exception as e:
            print(f"[SIM_1 HEAD WARN] {e}")

    def sim_2_gesture(self):
        # Buffer to allow camera stream connections to settle on the USB bus
        time.sleep(0.5)

        self.open_eyes()
        self.center_all()
        self.talking_both_arms()
        self.center_all()
        self.look_point_right()
        time.sleep(1)
        self.talking_right_arm() # currently hardcoded for default LEFT EYE
        self.center_all()
        self.talking_left_arm()
        self.center_all()

    def sim_3_gesture(self):
        # Buffer to allow camera stream connections to settle on the USB bus
        time.sleep(0.5)

        self.open_eyes()
        self.center_all()
        self.talking_both_arms()
        time.sleep(3)
        self.center_all()
        self.talking_left_arm()
        time.sleep(3)
        self.talking_right_arm()
        time.sleep(1)
        self.center_all()
        self.celebrate_arms_up()
        self.talking_left_arm()
        time.sleep(2)
        self.center_all()

    def overall_outro(self): # audio is 8 sec long
        print('overall_outro')
        self.open_eyes()
        self.center_all()
        self.talking_both_arms()
        self.blinking(1)
        self.center_all()
        self.celebrate_arms_up()
        self.center_all()
        self.blinking(2)
        self.close_eyes()

    def show_belly_image(self, filename: str, duration: float=3.0, blocking: bool=False):
        """
        Display any graphic on the robot's belly screen via VLC.
        Non-blocking so arm/head movements and speech can run simultaneously.
        """
        image_path = os.path.join(BASE_DIR, "static", "media", filename)
        print(f"BELLY DISPLAY: {image_path} ({duration}s)")
        
        if MEDIA_AVAILABLE and media_player:
            try:
                media_player.play_image(
                    image_path=image_path,
                    duration=duration,
                    fullscreen=True,
                    blocking=blocking
                )
            except Exception as err:
                print(f"[BELLY ERROR] VLC playback error: {err}")
        else:
            print(f"  [SIMULATION] Would show belly graphic: {filename}")    

    def countdown_gesture(self):
        print('TIMER BAR GESTURE')
        
        self.show_belly_image("YourTurnToAnswer.png", duration=9.0, blocking=False)
        interruptible_sleep(9.0)

    def show_RS(self, duration: float=3.0, **kwargs):
        print("SHOW RS")

        self.show_belly_image("AnswerRSEye.png", duration=duration, blocking=False)

    def show_LS(self, duration: float=3.0, **kwargs):
        print("SHOW LS")

        self.show_belly_image("AnswerLSEye.png", duration=duration, blocking=False)

    def play_sound(self, filename: str, blocking: bool = False):
        """Play sound through the onboard speaker."""
        audio_path = os.path.join(BASE_DIR, "static", "media", "audio", filename)
        if not os.path.exists(audio_path):
            audio_path = os.path.join(BASE_DIR, "static", "media", filename)
            
        print(f"ROBOT AUDIO: {audio_path}")
        if MEDIA_AVAILABLE and media_player:
            media_player.play_audio(audio_path, blocking=blocking)
        else:
            print(f"  [SIMULATION] Would play sound: {filename}")

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
            torso_motors.stop_arm_motions()
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
    'talking_both_arms': gesture_controller.talking_both_arms,
    'eyes_left': gesture_controller.eyes_left,
    'eyes_right': gesture_controller.eyes_right,
    'turn_head_left': gesture_controller.turn_head_left,
    'turn_head_right': gesture_controller.turn_head_right,
    'game_tts_1_prompt': gesture_controller.game_tts_1_prompt,
    'game_tts_1_answer': gesture_controller.game_tts_1_answer,
    'game_tts_2_prompt': gesture_controller.game_tts_2_prompt,
    'game_tts_2_answer': gesture_controller.game_tts_2_answer,
    'game_tts_3_prompt': gesture_controller.game_tts_3_prompt,
    'game_tts_3_answer': gesture_controller.game_tts_3_answer,
    'game_tts_4_prompt': gesture_controller.game_tts_4_prompt,
    'game_tts_4_answer': gesture_controller.game_tts_4_answer,
    'game_tts_5_prompt': gesture_controller.game_tts_5_prompt,
    'game_tts_5_answer': gesture_controller.game_tts_5_answer,
    'video_tts_all': gesture_controller.video_tts_all,
    'video_tts_1': gesture_controller.video_tts_1,
    'video_tts_2': gesture_controller.video_tts_2,
    'video_tts_3': gesture_controller.video_tts_3,
    'video_tts_4': gesture_controller.video_tts_4,
    'outro_game': gesture_controller.outro_game,
    'show_belly_image': gesture_controller.show_belly_image,
    'countdown_gesture': gesture_controller.countdown_gesture,
    'show_RS': gesture_controller.show_RS,
    'show_LS': gesture_controller.show_LS,
    'overall_intro_tts': gesture_controller.overall_intro_tts,
    'intro_game': gesture_controller.intro_game,
    'overall_outro': gesture_controller.overall_outro,
    'blink_test': gesture_controller.blink_test,
    'pitch_tester': gesture_controller.pitch_tester,
    'blinking': gesture_controller.blinking,
    'close_eyes': gesture_controller.close_eyes,
    'open_eyes': gesture_controller.open_eyes,
    'sim_1_gesture' : gesture_controller.sim_1_gesture,
    'sim_2_gesture' : gesture_controller.sim_2_gesture,
    'sim_3_gesture' : gesture_controller.sim_3_gesture
}


def execute_gesture(gesture_name, **kwargs):
    """
    Execute a gesture by name with optional parameters.
    Runs gesture in a separate process for easy termination.
    
    Args:
        gesture_name (str): Name of the gesture to execute
        **kwargs: Optional parameters to pass to the gesture (e.g., video_path)
        
    Returns:
        tuple: (process object, result dict) where result has status and message
    """
    if gesture_name not in GESTURES:
        return None, {
            'status': 'error',
            'message': f'Gesture "{gesture_name}" not found. Available gestures: {list(GESTURES.keys())}'
        }
    
    try:
        # Get the gesture function
        gesture_func = GESTURES[gesture_name]
        
        # Create a wrapper function that can be run in a process
        def gesture_wrapper():
            # Start idle motions in this subprocess (safe: shares motor instances)
            subprocess_idle_threads = []
            if MOTORS_AVAILABLE:
                try:
                    # Start idle threads in this subprocess
                    Idle_paused.set()  # Enable idle motions
                    eyebrow_thread = threading.Thread(target=idle_eyebrow_motion, daemon=True)
                    yaw_thread = threading.Thread(target=idle_head_yaw_motion, daemon=True)
                    # eyebrow_thread.start()
                    # yaw_thread.start()
                    subprocess_idle_threads = [eyebrow_thread, yaw_thread]
                except Exception as e:
                    print(f"[GESTURE] Could not start idle motions: {e}")
            
            # Setup signal handler for graceful shutdown
            def signal_handler(signum, frame):
                print(f"[GESTURE] Received SIGTERM, cleaning up motors...")
                # Stop idle motions
                Idle_paused.clear()
                # Cleanly close motor connections
                try:
                    if torso_motors:
                        try:
                            # Just stop power; do not close pigpio connection from the child
                            torso_motors.release_motors()
                        except Exception as e:
                            print(f"[GESTURE] Error releasing torso motors: {e}")
                except Exception as e:
                    print(f"[GESTURE] Error during motor cleanup: {e}")
                sys.exit(0)  # Exit gracefully
            
            # Register signal handler (only works on Unix/Linux)
            try:
                signal.signal(signal.SIGTERM, signal_handler)
            except (ValueError, RuntimeError):
                # Signal handling not available on Windows
                pass
            
            # Execute the gesture
            try:
                if kwargs:
                    gesture_func(**kwargs)
                else:
                    gesture_func()
            except Exception as e:
                print(f"[GESTURE] Error executing gesture: {e}")
                raise
            finally:
                # Stop idle motions when gesture completes
                Idle_paused.clear()
        
        # Run gesture in a separate process
        process = Process(target=gesture_wrapper, daemon=False)
        process.start()
        
        # Return process immediately without waiting
        # The server will handle waiting for the process asynchronously
        result = {
            'status': 'success',
            'message': f'Gesture "{gesture_name}" started'
        }
        
        return process, result
    except Exception as e:
        return None, {
            'status': 'error',
            'message': f'Error executing gesture "{gesture_name}": {str(e)}'
        }


def get_available_gestures():
    """Get list of available gestures."""
    return list(GESTURES.keys())
