import os
import sys
import time
import random
import threading
import multiprocessing
import subprocess
from pydub import AudioSegment
from pydub.playback import play
import vlc
import pygame

from mode_config import ModeManager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from control_modules.head_control import HeadMotors
from control_modules.torso_control import TorsoMotors

mode_manager = ModeManager()
head_motors = HeadMotors()
torso_motors = TorsoMotors()
start_exp = False #should be false
audio_playing = False
nextsection = False
jazz1 = None
start_cond = "c3"

############################################################
# Arm Movement Functions
############################################################

def arm_raise_right():
    """
    Raise right arm of Mirrly, then wait for 0.5 seconds.
    """
    torso_motors.arm_move("arm_r", 90, 0.01)
    time.sleep(0.5)

def arm_lower_right():
    """
    Lower right arm of Mirrly, then wait for 0.5 seconds.
    """
    torso_motors.arm_move("arm_r", 170, 0.01)
    time.sleep(0.5)

def arm_raise_left():
    """
    Raise left arm of Mirrly, then wait for 0.5 seconds.
    """
    torso_motors.arm_move("arm_l", 160, 0.01)
    time.sleep(0.5)

def arm_lower_left():
    """
    Lower left arm of Mirrly, then wait for 0.5 seconds.
    """
    torso_motors.arm_move("arm_l", 80, 0.01)
    time.sleep(0.5)

def arm_raise_both():
    """
    Raise both arms of Mirrly, then wait for 0.5 seconds.
    """
    torso_motors.arm_move("arm_r", 90, 0.01)
    torso_motors.arm_move("arm_l", 160, 0.01)
    time.sleep(0.5)

def arm_lower_both():
    """
    Lower both arms of Mirrly, then wait for 0.5 seconds.
    """
    torso_motors.arm_move("arm_r", 170, 0.01)
    torso_motors.arm_move("arm_l", 80, 0.01)
    time.sleep(0.5)


############################################################
# Base Movement Functions
############################################################

def rotate_base_left():
    """
    Rotate Mirrly's base to the left, robot should stay in place, 
    then wait for 0.5 seconds to ensure that movement is finished.
    """
    torso_motors.move("rotate_left", 0.5) #move takes which motor and speed, 
    #TODO: check if speed is correct; TODO: check if this moves in place
    time.sleep(0.5)

def rotate_base_right():
    """
    Rotate Mirrly's base to the right, robot should stay in place, 
    then wait for 0.5 seconds to ensure that movement is finished.
    """
    torso_motors.move("rotate_right", 0.5) #move takes which motor and speed, 
    #TODO: check if speed is correct; TODO: check if this moves in place
    time.sleep(0.5)

def move_forward(distance):
    """
    Move Mirrly forward by the specified distance in ...
    TODO: check for distance; implement distance parameter (using time?)
    """
    torso_motors.move("forward", 0.5) #move takes which motor and speed, 
    #TODO: check if speed is correct; TODO: if function also stops motors

def move_backward(distance):
    """
    Move Mirrly backward by the specified distance in ...
    TODO: check for distance; implement distance parameter (using time?)
    """
    torso_motors.move("backward", 0.5) #move takes which motor and speed, 
    #TODO: check if speed is correct; TODO: if function also stops motors



############################################################
# Main
############################################################
if __name__ == "__main__":
    # Example usage of arm movement functions
    arm_raise_right()
    arm_lower_right()
    arm_raise_left()
    arm_lower_left()
    arm_raise_both()
    arm_lower_both()

    # Example usage of base movement functions
    rotate_base_left()
    rotate_base_right()
    move_forward(1)  # Move forward by 1 unit (to be defined)
    move_backward(1) # Move backward by 1 unit (to be defined)