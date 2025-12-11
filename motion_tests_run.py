# run 'sudo pigpiod' every time doing smth w motors - prevents jitter
# run 'sudo shutdown -h now' AND WAIT FOR SCREEN FULLY OFF every time power down - safe RPi power down
# run in terminal: ctrl+C to end after program done

# mirrly will stand to the left side of the TV screen from participant POV
# from mirrly POV, the scdreen will be to the right

import os
import sys
import time
import random
import threading
import multiprocessing

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from control_modules.head_control import HeadMotors
from control_modules.torso_control import TorsoMotors
from robot_gestures import GestureController, LIMITS, PITCH_SPEED, EYELID_SPEED, head_motors, torso_motors #

robot_motions = GestureController() # THIS ALREADY INITS head_motors & torso_motors; doing it again here will lock GPIO

start_exp = False
start_cond = "test"

'''
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

def center_all():
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

def look_point_left():
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

def look_point_right():
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

def celebrate_arms_up():
    head_motors.move("head_yaw", LIMITS["head_yaw"]["center"], 400)
    head_motors.move("head_pitch", LIMITS["head_pitch"]["up"], PITCH_SPEED)
    head_motors.move("eye_self", LIMITS["eye_self"]["center"], 500)
    head_motors.move("eye_brow_l", LIMITS["eye_brow_l"]["open"], EYELID_SPEED)
    head_motors.move("eye_brow_r", LIMITS["eye_brow_r"]["open"], EYELID_SPEED)

    torso_motors.arm_move("arm_r", LIMITS["arm_r"]["up"], 0.01)
    torso_motors.arm_move("r_shoulder", LIMITS["r_shoulder"]["front"], 0.01)
    torso_motors.arm_move("arm_l", LIMITS["arm_l"]["up"], 0.01)
    torso_motors.arm_move("l_shoulder", LIMITS["l_shoulder"]["front"], 0.01)

    time.sleep(2)

def sad_look_down():
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

def talking_left_arm():
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

def talking_right_arm():
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

def eyes_left():
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
'''

def game_tts_1_prompt(): # audio is 15 sec long
    robot_motions.talking_both_arm()
    robot_motions.center_all()
    time.sleep(1)

    # In his right eye, ...
    robot_motions.talking_right_arm()
    robot_motions.center_all()
    time.sleep(1)

    # ... made his vision cloudy
    robot_motions.sad_look_down()
    robot_motions.center_all()

    # Which of Mikey's eyes...
    robot_motions.look_point_left()
    robot_motions.center_all()

def game_tts_1_answer(): # audio is 8 sec long
    robot_motions.talking_left_arm()
    robot_motions.center_all()
    time.sleep(1)

    robot_motions.celebrate_arms_up()
    robot_motions.center_all()

def game_tts_2_prompt(): # audio is 14 sec long
    # pause until when they're playing with...
    time.sleep(1)
    time.sleep(1)
    robot_motions.celebrate_arms_up()
    robot_motions.center_all()
    time.sleep(1)

    # covered part of their vision in their left eye
    robot_motions.talking_left_arm()
    robot_motions.center_all()

    time.sleep(1)
    # which of Alex's eyes...
    robot_motions.look_point_left()
    robot_motions.center_all()

def game_tts_2_answer(): # audio is 6 sec long
    robot_motions.talking_right_arm()
    robot_motions.center_all()
    robot_motions.talking_left_arm()
    robot_motions.center_all()

def game_tts_3_prompt(): # audio is 15 sec long

    #start when Fiona used to have an
    robot_motions.talking_right_arm()
    robot_motions.center_all()

    # which eye do you think...
    robot_motions.look_point_left()
    robot_motions.center_all()

def game_tts_3_answer(): # audio is 7 sec long
    robot_motions.talking_left_arm()
    robot_motions.center_all()
    robot_motions.celebrate_arms_up()
    robot_motions.center_all()

def game_tts_4_prompt(): # audio is 16 sec long
    robot_motions.celebrate_arms_up()
    robot_motions.center_all()

    # She used to get...
    robot_motions.talking_right_arm()
    robot_motions.talking_left_arm()
    robot_motions.center_all()

    robot_motions.look_point_right()
    robot_motions.center_all()

def game_tts_4_answer(): # audio is 7 sec long
    robot_motions.talking_left_arm()
    robot_motions.center_all()
    robot_motions.celebrate_arms_up()
    robot_motions.center_all()

def game_tts_5_prompt(): # audio is 14 sec long
    robot_motions.celebrate_arms_up()
    robot_motions.center_all()

    # Daniel's vision is blury
    robot_motions.talking_left_arm()
    robot_motions.center_all()

    # which eye is should
    robot_motions.look_point_left()
    robot_motions.center_all()

def game_tts_5_answer(): # audio is 6 sec long
    robot_motions.talking_right_arm()
    robot_motions.center_all()
    robot_motions.talking_left_arm()
    robot_motions.center_all()


def video_tts_1(): # audio is 48 sec long
    robot_motions.talking_right_arm()
    robot_motions.center_all()
    #
    robot_motions.look_point_left()
    robot_motions.center_all()
    #
    robot_motions.celebrate_arms_up()
    robot_motions.center_all()
    #
    time.sleep(3)
    robot_motions.talking_left_arm()
    robot_motions.center_all()
    #
    robot_motions.talking_left_arm()
    robot_motions.talking_right_arm()
    robot_motions.center_all()
    #
    robot_motions.talking_right_arm()
    robot_motions.center_all()

def video_tts_2(): # audio is 13 sec long
    robot_motions.celebrate_arms_up()
    time.sleep(3)
    robot_motions.center_all()
    #
    robot_motions.talking_right_arm()
    robot_motions.center_all()

def video_tts_3(): # audio is 56 sec long
    robot_motions.celebrate_arms_up()
    time.sleep(2)
    robot_motions.center_all()
    #
    robot_motions.talking_left_arm()
    time.sleep(2)
    robot_motions.center_all()
    #
    robot_motions.talking_right_arm()
    robot_motions.center_all()
    #
    robot_motions.talking_right_arm()
    time.sleep(3)
    robot_motions.center_all()
    #
    robot_motions.celebrate_arms_up()
    time.sleep(2)
    robot_motions.center_all()
    #
    robot_motions.talking_left_arm()
    time.sleep(2)
    robot_motions.center_all()
    #
    robot_motions.talking_right_arm()
    time.sleep(2)
    robot_motions.center_all()

def video_tts_4(): # audio is 21 sec long
    robot_motions.celebrate_arms_up()
    time.sleep(4)
    #
    robot_motions.look_point_right()
    robot_motions.center_all()

def outro_game():
    robot_motions.celebrate_arms_up()
    robot_motions.center_all()

##### idle functions part of threading structure, so kept in 

def keyboard_listener(paused, eyebrow_process, yaw_process, rsh_process):
    global start_exp
    global start_cond
    paused_state = True  # track the paused state
    while True:
        user_input = input("Enter command ('test' or 'vid#' (# 1 to 4) to start, 'p' to toggle pausing, 'q' to quit): ").lower()
        if user_input == 'test' or 'vid1' or 'vid2' or 'vid3' or 'vid4':
            start_exp = True
            start_cond = user_input
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
#####

def terminate_program():
    print("Terminating program.")
    '''
    torso_motors.release_motors()
    torso_motors.release_hands('all')
    head_motors.close()
    '''
    robot_motions.cleanup() # already does the above
    sys.exit(0)
        
if __name__ == "__main__":
    
    paused = multiprocessing.Event() # like a traffic light to allow actions
    paused.set()

    random_brow_process = multiprocessing.Process(target=eye_brow_idle, args=(paused,))
    random_yaw_roll_process = multiprocessing.Process(target=yaw_roll, args=(paused,))
    random_rsh_process = multiprocessing.Process(target=hand_shoulder_idle, args=(paused,))
        
    try:
        # Start a separate thread to listen for the keyboard inputs
        keyboard_thread = threading.Thread(target=keyboard_listener, args=(paused, random_brow_process,
                                                                            random_yaw_roll_process, random_rsh_process))
        keyboard_thread.daemon = True
        keyboard_thread.start()
        
        # Wait until the experiment starts
        print("Enter 'test', 'game1', 'game2', 'game3', or 'game4' to start: ")
        while not start_exp:
            time.sleep(1)
        
        if start_cond == 'test':
            paused.clear()
            time.sleep(1)

            print("OUTRO GAME")
            outro_game()

            paused.set()
        time.sleep(1)

        if start_cond == 'g1':
            paused.clear()
            time.sleep(1)

            print("game_tts_1")
            game_tts_1_prompt()

            paused.set()
        time.sleep(1)

        if start_cond == 'f1':
            paused.clear()
            time.sleep(1)

            print("game_tts_1")
            game_tts_1_answer()

            paused.set()
        time.sleep(1)

        if start_cond == 'game2':
            paused.clear()
            time.sleep(1)

            print("game_tts_2")
            game_tts_2_prompt()

            paused.set()
        time.sleep(1)

        if start_cond == 'game3':
            paused.clear()
            time.sleep(1)

            print("game_tts_3")
            game_tts_3_prompt()

            paused.set()
        time.sleep(1)

        if start_cond == 'game4':
            paused.clear()
            time.sleep(1)

            print("game_tts_4")
            game_tts_4_prompt()

            paused.set()
        time.sleep(1)
        
        while True:
            time.sleep(1)
        
    except KeyboardInterrupt:
        print(f"\nProgram ended by keyboard interrupt")
        terminate_program()
