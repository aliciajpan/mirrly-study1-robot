#!/usr/bin/env python3

import time
import math
import subprocess
import threading
#import pyfirmata
#from pyfirmata import util
from gpiozero import Servo, AngularServo, PWMOutputDevice
from gpiozero.pins.pigpio import PiGPIOFactory

def custom_range(start, end, step=1):
    if start < end:
        while start <= end:
            yield start
            start += step
    else:
        while start >= end:
            yield start
            start -= step
            
class TorsoMotors(): 
    """This class manages robot's foot motions."""

    def __init__(self):
        # Define the pins used by the motor driver
        self.PWM1 = 12
        self.PWM2 = 13
        self.PWM3 = 18
        self.PWM4 = 19
        
        # Hand pins
        # self.hs_pins = [31, 11 ,13, 15] #BOARD scheme l_hand, shoulder, r_hand, Shoulder
        self.hs_pins = [6, 27 ,17, 22] #BOARD scheme
        self.s_positions = [0, 0, 0, 0] # arm_l, l_shoulder, arm_r, r_shoulder
        self.read_positions()

        # Connect to the Arduino
        """
        self.board = pyfirmata.Arduino('/dev/ttyACM0')  # Update the port if necessary
        it = util.Iterator(self.board)
        it.start()
        """
        
        # Configure the pins # Foots
        self.M1A = PWMOutputDevice(self.PWM1)
        self.M1B = PWMOutputDevice(self.PWM2)
        self.M2A = PWMOutputDevice(self.PWM3)
        self.M2B = PWMOutputDevice(self.PWM4)
        
        # Configure pins for # Hands 
        #GPIO.setmode(GPIO.BOARD)
        
        # Set up additional pins for servos
        #GPIO.setup(self.hs_pins, GPIO.OUT)
            
        #self.l_hand = GPIO.PWM(self.hs_pins[0], 50) # Left Hand 6.5-12
        #self.l_shoulder = GPIO.PWM(self.hs_pins[1], 50) # Left Shoulder 3-12.5
        #self.r_hand = GPIO.PWM(self.hs_pins[2], 50) # Right Hand 2.5-7.5
        #self.r_shoulder = GPIO.PWM(self.hs_pins[3], 50) # Right Shoulder 3-12.5
        
        # self.l_hand.start(0)
        # self.r_hand.start(0)
        # self.l_shoulder.start(0)
        # self.r_shoulder.start(0)
        
        # Arms Configurations GPIOZero
        """
        # Bash command to be executed
        bash_command = "sudo pigpiod"

        # Run the Bash command
        try:
            subprocess.run(bash_command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running the command: {e}")
        """
        
        self.factory = PiGPIOFactory() # For Jitter Reduction
        self.factory2 = PiGPIOFactory() # For Jitter Reduction
        self.factory3 = PiGPIOFactory() # For Jitter Reduction
        self.factory4 = PiGPIOFactory() # For Jitter Reduction
        time.sleep(1)
        
        self.l_hand = AngularServo(self.hs_pins[0], min_pulse_width=0.0005, 
                            max_pulse_width=0.0025, pin_factory=self.factory,
                            min_angle=0, max_angle= 180
                            , initial_angle=self.s_positions[0])
        time.sleep(1)

        self.r_hand = AngularServo(self.hs_pins[1], min_pulse_width=0.0005, 
                            max_pulse_width=0.0025, pin_factory=self.factory2
                            ,min_angle=0, max_angle=180
                            , initial_angle=self.s_positions[2])
        time.sleep(1)

        self.l_shoulder = AngularServo(self.hs_pins[2], min_pulse_width=0.0005, 
                            max_pulse_width=0.0025, pin_factory=self.factory3
                            ,min_angle=0, max_angle=180
                            , initial_angle=self.s_positions[1])
        time.sleep(1)

        self.r_shoulder = AngularServo(self.hs_pins[3], min_pulse_width=0.0005, 
                            max_pulse_width=0.0025, pin_factory=self.factory4,
                            min_angle=0, max_angle=180, initial_angle=self.s_positions[3])
        
        # Set the initial motor speeds
        self.speed1 = 255
        self.speed2 = 255

        # Track active arm motion threads for safe cancellation/overlap handling
        self.arm_threads = {}
        self.arm_stop_flags = {}
        
    def read_positions(self, filename="./positions.txt"):
        import os
        # Create default positions file if it doesn't exist
        if not os.path.exists(filename):
            with open(filename, "w") as file:
                for position in self.s_positions:
                    file.write(str(position) + "\n")
        
        with open(filename, "r") as file:
            for i, line in enumerate(file):
                self.s_positions[i] = int(line.strip())

    def update_positions(self, new_positions, filename="./positions.txt"):
        self.s_positions = new_positions
        #print(self.s_positions)
        with open(filename, "w") as file:
            for position in self.s_positions:
                file.write(str(position) + "\n")
        
    def _component_index(self, comp):
        mapping = {
            "arm_l": 0,
            "l_shoulder": 1,
            "arm_r": 2,
            "r_shoulder": 3,
        }
        return mapping.get(comp)

    def stop_arm_motions(self):
        """Cancel and join any active arm motion threads."""
        for comp, stop_flag in list(self.arm_stop_flags.items()):
            stop_flag.set()
        for comp, thread in list(self.arm_threads.items()):
            thread.join(timeout=0.2)
        self.arm_threads.clear()
        self.arm_stop_flags.clear()

    def arm_motion_smooth(self, comp, servo, initial, angle, speed=0.01):
        """Move a servo smoothly using a cancellable thread, allowing concurrency across arms."""

        # If a motion is already running for this component, cancel it first
        if comp in self.arm_stop_flags:
            self.arm_stop_flags[comp].set()
        if comp in self.arm_threads:
            self.arm_threads[comp].join(timeout=0.2)

        stop_flag = threading.Event()
        self.arm_stop_flags[comp] = stop_flag

        idx = self._component_index(comp)

        def motion_smooth():
            for i in custom_range(initial, angle):
                if stop_flag.is_set() or getattr(servo, "closed", False):
                    return
                try:
                    servo.angle = i
                except Exception:
                    return
                time.sleep(speed)
            # Update stored position only if we reached the target
            if not stop_flag.is_set() and idx is not None:
                self.s_positions[idx] = angle
                self.update_positions(self.s_positions)
            # Clean up tracking for this component when done
            if self.arm_threads.get(comp) is threading.current_thread():
                self.arm_threads.pop(comp, None)
                self.arm_stop_flags.pop(comp, None)

        t = threading.Thread(target=motion_smooth, daemon=True)
        self.arm_threads[comp] = t
        t.start()
        
    def arm_move(self, comp, angle, speed):
        """Start a cancellable smooth motion for a specific arm/shoulder component."""
        self.read_positions()
        if comp == "r_shoulder":
            initial = getattr(self.r_shoulder, "angle", self.s_positions[3])
            self.arm_motion_smooth(comp, self.r_shoulder, initial, angle, speed)
        elif comp == "l_shoulder":
            initial = getattr(self.l_shoulder, "angle", self.s_positions[1])
            self.arm_motion_smooth(comp, self.l_shoulder, initial, angle, speed)
        elif comp == "arm_r":
            initial = getattr(self.r_hand, "angle", self.s_positions[2])
            self.arm_motion_smooth(comp, self.r_hand, initial, angle, speed)
        elif comp == "arm_l":
            initial = getattr(self.l_hand, "angle", self.s_positions[0])
            self.arm_motion_smooth(comp, self.l_hand, initial, angle, speed)
        else:
            return
        # Position updates happen in the motion thread when it completes
        
    def hands_freq(self, comp, n):
        if comp == "r_shoulder":
            self.r_shoulder.ChangeFrequency(n)
        elif comp == "l_shoulder":
            self.l_shoulder.ChangeFrequency(n)
        elif comp == "arm_r":
            self.r_hand.ChangeFrequency(n)
        elif comp == "arm_l":
            self.l_hand.ChangeFrequency(n)
        elif comp == "all":
            self.l_hand.ChangeFrequency(n)
            self.r_hand.ChangeFrequency(n)
            self.l_shoulder.ChangeFrequency(n)
            self.r_shoulder.ChangeFrequency(n)
            
    def release_hands(self, comp):
        # Stop any ongoing arm motions before closing servos
        self.stop_arm_motions()

        if comp == "r_shoulder":
            self.r_shoulder.close()
        elif comp == "l_shoulder":
            self.l_shoulder.close()
        elif comp == "arm_r":
            self.r_hand.close()
        elif comp == "arm_l":
            self.l_hand.close()
        elif comp == "all":
            self.l_hand.close()
            self.r_hand.close()
            self.l_shoulder.close()
            self.r_shoulder.close()
            
    def move(self, motor, speed):
        pwm_speed = float(speed) / 255.0
        
        if motor == "live":
            print(speed)
            if int(speed['x']) < 80 and int(speed['x']) > -80:
                if(speed['y']) > 0:
                    print("backward")
                    self.M1A.write(float(speed['y'])/255)
                    self.M1B.write(0)
                    self.M2A.write(0)
                    self.M2B.write(float(speed['y'])/255)
                else:
                    print("forward")
                    self.M1A.write(0)
                    self.M1B.write(float(-speed['y'])/255)
                    self.M2A.write(float(-speed['y'])/255)
                    self.M2B.write(0)
            elif int(speed['y']) < 80 and int(speed['y']) > -80:
                if(speed['x']) > 0:
                    print("right")
                    self.M1A.write(0)
                    self.M1B.write(0)
                    self.M2A.write(float(speed['x'])/255)
                    self.M2B.write(0)
                else:
                    print("left")
                    self.M1A.write(0)
                    self.M1B.write(-float(speed['x'])/255)
                    self.M2A.write(0)
                    self.M2B.write(0)
            else:
                    if int(speed['x']) > 0:
                        if int(speed['y']) < 0:
                            print("top-right")
                            self.M1B.write(0)
                            self.M2B.write(0)
                            self.M1A.write(-float(speed['y'])/255)
                            self.M2A.write(float(speed['x'])/255)
                        else:
                            print("back-right")
                            self.M2A.write(0)
                            self.M2B.write(0)
                            self.M1A.write(float(speed['y'])/255)
                            self.M2A.write(float(speed['x'])/255)
                    else:
                        if int(speed['y']) < 0:
                            print("top-left")
                            self.M1A.write(0)
                            self.M2A.write(0)
                            self.M2B.write(-float(speed['y'])/255)
                            self.M1B.write(-float(speed['x'])/255)
                        else:
                            print("back-left")
                            self.M1A.write(0)
                            self.M2A.write(0)
                            self.M1B.write(float(speed['y'])/255)
                            self.M2B.write(-float(speed['x'])/255)
        if motor == "forward":
            # Set speed
            if speed != self.speed1:
                self.speed1 = int(speed)
                self.speed2 = int(speed)
            # Run the motors
            self.M1A.value = 0
            self.M1B.value = pwm_speed
            self.M2A.value = pwm_speed
            self.M2B.value = 0
        elif motor == "backward":
            # Set speed
            if speed != self.speed1:
                self.speed1 = int(speed)
                self.speed2 = int(speed)
            # Run the motors
            self.M1A.value = pwm_speed
            self.M1B.value = 0
            self.M2A.value = 0
            self.M2B.value = pwm_speed
        elif motor == "rotate_right":
            # Set speed
            if speed != self.speed1:
                self.speed1 = int(speed)
                self.speed2 = int(speed)
            # Run the motors
            self.M1A.value = 0
            self.M1B.value = 0
            self.M2A.value = pwm_speed
            self.M2B.value = 0
        elif motor == "rotate_left":
            # Set speed
            if speed != self.speed1:
                self.speed1 = int(speed)
                self.speed2 = int(speed)
            # Run the motors
            self.M1A.value = 0
            self.M1B.value = pwm_speed
            self.M2A.value = 0
            self.M2B.value = 0
        elif motor == "rotate_left_b":
            # Set speed
            if speed != self.speed1:
                self.speed1 = int(speed)
                self.speed2 = int(speed)
            # Run the motors
            self.M1A.value = 0
            self.M1B.value = 0
            self.M2A.value = 0
            self.M2B.value = pwm_speed
        elif motor == "rotate_right_b":
            # Set speed
            if speed != self.speed1:
                self.speed1 = int(speed)
                self.speed2 = int(speed)
            # Run the motors
            self.M1A.value = pwm_speed
            self.M1B.value = 0
            self.M2A.value = 0
            self.M2B.value = 0  
    def release_motors(self):
        # Release the motors
        time.sleep(0.2) # Should be considered or it will be not work consistent
        self.M1A.value = 0
        self.M1B.value = 0
        self.M2A.value = 0
        self.M2B.value = 0
        print("motors release")

    def close(self):
        # Disconnect from the Arduino
        self.board.exit()

