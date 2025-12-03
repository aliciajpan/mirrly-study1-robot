import sys
import time
import random
import threading
import multiprocessing

from head_control import HeadMotors
from torso_control import TorsoMotors

head_motors = HeadMotors()
torso_motors = TorsoMotors()

LIMITS = { # ASK: DIRECTIONS OF THESE
    # l and r from mirrly pov!
    "head_yaw":   {"left": 590, "center": 807, "right": 970},  # left / right ASK: 180 used for center later...?
    "head_pitch": {"up": 118, "center": 200, "down": 279},  # up / down
    "eye_self":   {"left": 221, "center": 245, "right": 268},  # eyeball
    "eye_brow_l": {"open": 210, "center": 350, "close": 467},  # left eyelid
    "eye_brow_r": {"open": 343, "center": 343, "close": 643},  # right eyelid
    "arm_r": {"up": 90, "rest": 170, "down": 170},  # right arm (confirmed)
    "arm_l": {"up": 160, "rest": 80, "down": 80},  # right arm (confirmed)
    "r_shoulder": {"up": 160, "rest": 70, "down": 70},  # right arm
    "l_shoulder": {"up": 60, "rest": 160, "down": 160},  # right arm
} 

start_exp = False # should be false
start_cond = "test"

def center_all():
    print("CENTRE ALL")
    # head motors: larger speed # = faster
    head_motors.move("head_yaw", LIMITS["head_yaw"]["center"], 400)
    head_motors.move("head_pitch", LIMITS["head_pitch"]["center"], 400)
    head_motors.move("eye_self", LIMITS["eye_self"]["center"], 400)
    head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["center"], 400)
    head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["center"], 400)

    # ASK: torso motors: larger speed # = slower ?
    torso_motors.arm_move("arm_r", LIMITS["arm_r"]["rest"], 0.01)
    torso_motors.arm_move("arm_l", LIMITS["arm_l"]["rest"], 0.01)
    torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["rest"], 0.01)
    torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["rest"], 0.01)

    time.sleep(1.0)

def look_point_left():
    head_motors.move("head_yaw", LIMITS["head_yaw"]["left"], 300)
    head_motors.move("eye_self", LIMITS["eye_self"]["left"], 300)
    torso_motors.arm_move("arm_l", LIMITS["arm_l"]["up"], 0.01)
    torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["up"], 0.01)
    time.sleep(2)

def look_point_right():
    head_motors.move("head_yaw", LIMITS["head_yaw"]["right"], 300)
    head_motors.move("eye_self", LIMITS["eye_self"]["right"], 300)
    torso_motors.arm_move("arm_r", LIMITS["arm_r"]["up"], 0.01)
    torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["up"], 0.01)
    time.sleep(2)

def keyboard_listener(paused, eyebrow_process, yaw_process, rsh_process):
    global start_exp
    global start_cond
    paused_state = True  # track the paused state
    while True:
        user_input = input("Enter command ('test' to start, 'p' to toggle pausing, 'q' to quit): ").lower()
        if user_input == 'test':
            start_exp = True
            start_cond = 'test'
            print("Test started.")
        elif user_input == 'p':
            if paused_state:
                paused.clear()  # resume the eyebrow process
                print("Program resumed.")
            else:
                paused.set()  # rause the eyebrow process
                print("Program paused.")
            paused_state = not paused_state  # toggle paused state
        elif user_input == 'q':
            eyebrow_process.terminate()
            eyebrow_process.join()  # ensure the process has terminated
            
            yaw_process.terminate()
            yaw_process.join()

            rsh_process.terminate()
            rsh_process.join()
            terminate_program()
            break

def eye_brow_idle(paused):
    while True:
        paused.wait()  # block the loop when the event is set (paused)
        probability = 0.07  # probability of eyebrow idle movement
        blink_speed = random.choice([800, 1000])
        if random.random() < probability:
            try:
                head_motors.move("eye_brow_l", 210, blink_speed - 100)
                time.sleep(0.01)
                head_motors.move("eye_brow_r", 510, blink_speed)
                time.sleep(0.4 if blink_speed == 1000 else 0.8 if blink_speed == 800 else 0.9)
                head_motors.move("eye_brow_l", 350, blink_speed - 100)
                time.sleep(0.01)
                head_motors.move("eye_brow_r", 343, blink_speed)
            except Exception as e:
                print(f"Error in eyebrow movement: {e}")
                time.sleep(0.01)
                continue
        time.sleep(0.5)

def yaw_roll(paused):
    while True:
        paused.wait()  # block the loop when the event is set (paused)
        probability = 0.07  # probability of eye movement
        if random.random() < probability:
            random_value = random.randint(0, 300)
            random_speed = random.randint(300, 500)
            head_motors.move("head_yaw", random_value, random_speed)
            random_rt = random.randint(1, 3)
            time.sleep(random_rt)
            head_motors.move("head_yaw", 180, random_speed)

        time.sleep(0.5)

def hand_shoulder_idle(paused):
    while True:
        paused.wait()  # block the loop when the event is set (paused)
        probability = 0.07  # probability of eyebrow idle movement
        movement_number = random.randint(1, 2)
        if random.random() < probability:
            try:
                if movement_number == 1:
                    torso_motors.arm_move("arm_r", 170, 0.01)  # 170 Down - 90 Up When screw is front
                    torso_motors.arm_move("arm_l", 80, 0.01)  # 160 Up - 80 Down When screw is front
                    time.sleep(0.5)
                    for i in range(4):
                        torso_motors.arm_move("r_shoulder", 90, 0.01)  # 70 cap front - 160 cap top
                        torso_motors.arm_move("l_shoulder", 140, 0.01)  # 160 cap front - 60 cap top
                        time.sleep(0.5)
                        torso_motors.arm_move("r_shoulder", 70, 0.01)  # 70 cap front - 160 cap top
                        torso_motors.arm_move("l_shoulder", 160, 0.01)  # 160 cap front - 60 cap top
                        time.sleep(0.5)
                elif movement_number == 2:
                    torso_motors.arm_move("arm_r", 170, 0.01)  # 170 Down - 90 Up When screw is front
                    torso_motors.arm_move("arm_l", 80, 0.01)  # 160 Up - 80 Down When screw is front
                    time.sleep(0.5)
                    for i in range(4):
                        torso_motors.arm_move("arm_r", 150, 0.01)  # 170 Down - 90 Up When screw is front
                        torso_motors.arm_move("arm_l", 100, 0.01)  # 160 Up - 80 Down When screw is front
                        time.sleep(0.5)
                        torso_motors.arm_move("arm_r", 170, 0.01)  # 170 Down - 90 Up When screw is front
                        torso_motors.arm_move("arm_l", 80, 0.01)  # 160 Up - 80 Down When screw is front
                        time.sleep(0.5)

                elif movement_number == 3:
                    pass
                elif movement_number == 4:
                    pass
                else:
                    pass
            except Exception as e:
                print(f"Error in hand_shoulder movement: {e}")
                time.sleep(0.01)
                continue
        time.sleep(0.5)

def terminate_program():
    print("Terminating program.")
    torso_motors.release_motors()
    torso_motors.release_hands('all')
    head_motors.close()
    sys.exit(0)
        
if __name__ == "__main__":
    
    paused = multiprocessing.Event() # like a traffic light to allow actions
    paused.set() # ASK: for multiprocessing.Event, is .set() stopping or allowing action? name is opposite
    # original experiment_run says this starts it paused

    random_brow_process = multiprocessing.Process(target=eye_brow_idle, args=(paused,))
    random_yaw_roll_process = multiprocessing.Process(target=yaw_roll, args=(paused,))
    random_rsh_process = multiprocessing.Process(target=hand_shoulder_idle, args=(paused,))
        
    try:
        # Start a separate thread to listen for the keyboard inputs
        keyboard_thread = threading.Thread(target=keyboard_listener, args=(paused, random_brow_process,
                                                                            random_yaw_roll_process, random_rsh_process))
        keyboard_thread.daemon = True
        keyboard_thread.start()
        
        # Wake up motion
        head_motors.move("eye_brow_l", 210, 500)
        head_motors.move("eye_brow_r", 510, 500)
        head_motors.move("head_pitch", 125, 800)
        head_motors.move("head_yaw", 180, 400)

        torso_motors.arm_move("arm_r", 170, 0.001)  # 170 Down - 90 Up When screw is front
        torso_motors.arm_move("arm_l", 80, 0.001)  # 160 Up - 80 Down When screw is front
        torso_motors.arm_move("r_shoulder", 70, 0.001)  # 70 cap front - 160 cap top -
        torso_motors.arm_move("l_shoulder", 160, 0.001)  # 160 cap front - 60 cap top
        
        # Wait until the experiment starts
        print("Enter 'test' to start...")
        while not start_exp:
            time.sleep(1)
        
        print("Start background idle motions")       
        random_brow_process.start()        
        random_yaw_roll_process.start()        
        random_rsh_process.start()
        
        if start_cond == 'test':
            print("Range of motion test")
            paused.clear()
            time.sleep(1)

            center_all()

            print("Testing Yaw")
            head_motors.move("head_yaw", LIMITS["head_yaw"]["left"], 300)
            time.sleep(1)
            head_motors.move("head_yaw", LIMITS["head_yaw"]["right"], 300)
            time.sleep(1)
            center_all()

            print("Testing Pitch")
            head_motors.move("head_pitch", LIMITS["head_pitch"]["down"], 100) # do slowly, motion is tough on motors
            time.sleep(1)
            head_motors.move("head_pitch", LIMITS["head_pitch"]["up"], 100)
            time.sleep(1)
            center_all()

            print("Testing Eyeballs")
            head_motors.move("eye_self", LIMITS["eye_self"]["left"], 400)
            time.sleep(1)
            head_motors.move("eye_self", LIMITS["eye_self"]["right"], 400)
            time.sleep(1)
            center_all()

            print("Testing Eyelids")
            head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["open"], 400)
            head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["open"], 400)
            time.sleep(1)
            head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["close"], 400)
            head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["close"], 400)
            time.sleep(1)
            center_all()

            print("Done range of motion test")

            print("Look and point left")
            look_point_left()
            center_all()

            print("Look and point right")
            look_point_right()
            center_all()

            time.sleep(1)
            paused.set()
        time.sleep(1)
        
        while True:
            time.sleep(1)
        
    except Exception as e:
        print(f"Exception occurred: {e}")
        terminate_program()
