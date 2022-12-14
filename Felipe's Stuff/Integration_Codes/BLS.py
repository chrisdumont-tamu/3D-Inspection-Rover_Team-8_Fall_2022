###############################
# THINGS TO KNOW
        # MOTOR INFO
# Sample for Sabertooth Simplified Serial
# Test w/ RPi3B+ -> USB to TTL 5V Cable -> Sabertooth 2X12
# USB to TTL Cable Hookup to Sabertooth: GND -> 0V, TX -> S1
# DIP Config (9600 Buad): 1UP - 2DOWN - 3 UP - 4DOWN - 5UP - 6UP

# M1: 1 - 127; 1 = full reverse, 64 = stop, 127 = full forward
# M2: 128 - 255; 128 = full reverse, 192 = stop, 255 = full forward
# M1 & M2; 0 = stop
#stop +/- 6 is good for slow movement
#Avoid going full speed

        # DISTANCE SENSOR INFO
#SENSOR 3
#Trigger=16
#Echo=18
#SENSOR 2
#Trigger=36
#Echo=31
#SENSOR 1
#Trigger=8
#Echo=38
#########################################################

#general imports for code functionality

import serial
import time
from time import sleep
import RPi.GPIO as GPIO
import Chris_Functions as CF
import pyrealsense2.pyrealsense2 as rs
import ML_Functions as mf

#setup serial functionality
port = "/dev/ttyUSB0"  #find available USB using "ls /dev/*USB* in terminal"
ser = serial.Serial()
ser.port = port
ser.close() 
ser.baudrate = 9600
ser.bytesize = serial.EIGHTBITS
ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE
ser.timeout = 1
ser.open()
ser.flushInput()
ser.flushOutput()

GPIO.setwarnings(False) #sets all gpio warnings to 0
GPIO.setmode(GPIO.BOARD) #sets gpio numbering system to match board numbers

#Define Constants
#Distance Sensors
  # trigger pins
Trigger1 = 8
Trigger2=36
Trigger3=16
  # echo pins
Echo1 = 38
Echo2=31
Echo3=18
#^^^^^^^^ Need to change GPIO 12/32 to different pins
v=10
avoid_distance=100

#Servo Controls
pan_s = 35 #GPIO for pan servo
tilt_s = 32 #GPIO for tilt servo
f_pwm = 50 #50Hz signal
delay = 0.0000000001 #delay for the created pwm
# Setup for Pan/Tilt Servos
def setup():#setup function
    global pwm #pwm global
    GPIO.setup(pan_s, GPIO.OUT)#setup pan output pin
    GPIO.setup(tilt_s, GPIO.OUT) #setup tilt output pin
    GPIO.setup(15,GPIO.OUT) # enable, was 22
    GPIO.setup(13,GPIO.OUT) # direction, was 21
    GPIO.setup(11,GPIO.OUT) # step, was 20

# Setup Distance Sensors
  # output pins
GPIO.setup(Trigger1, GPIO.OUT)
GPIO.setup(Trigger2,GPIO.OUT)
GPIO.setup(Trigger3, GPIO.OUT)
  # input pins
GPIO.setup(Echo1, GPIO.IN)
GPIO.setup(Echo2,GPIO.IN)
GPIO.setup(Echo3,GPIO.IN)

# Variables to keep track of
Aisle_Count = 1
Plant_Number = 1

## Upload Data to Database
# Constants
DYNAMODB_ENDPOINT = 'https://cnpu0bqb4i.execute-api.us-east-1.amazonaws.com/beta/items'
LOG_FILE_PATH = r'/home/pi/BOB_Inspection_Rover/logs/tomatoes_log.csv' # Path to CSV where data is exported


print("\nAll setups and constants declared successfully\n")


## Camera setup
# Create a pipeline object to own and handle realsnese camera
pipeline = rs.pipeline()

# Configure the streams
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.rgb8, 30)

# Begin streaming
pipeline.start(config)

# Perform color to depth alignment
align_to = rs.stream.color
align = rs.align(align_to)

print("Camera Successfully Streaming\n")

#Defines PWM Frequence for Pan/Tilt Servos
def setServoAngle(servo, angle):
    pwm = GPIO.PWM(servo, f_pwm) #setup output frequency
    pwm.start(8)
    dutyCycle = angle / 18. + 2.
    pwm.ChangeDutyCycle(dutyCycle)
    time.sleep(1.5)


def shawty(aisle, plant):
    print("\nMast moving upward\n") #start
    tic = int(time.perf_counter()) #timer start
    tac = 0.0 #total elapsed time initialized
    while tac < 10: #loop to run for 24 seconds
        GPIO.output(11,GPIO.HIGH) #step off
        sleep(delay)
        GPIO.output(11, GPIO.LOW) #step on
        sleep(delay)
        toc = int(time.perf_counter()) #timer end
        tac = toc - tic #total time elapsed 
        #print(tac)
    print(tac)
    print("\nMast stop for tomato scanning\n")
    #confid_rating = 75, desired confidence min
    i = 0 #direction identifier
    j = 0 #counter for loop iterations
    #while loop for running through directions
    #tic = time.perf_counter()
    setServoAngle(pan_s,76) #baseline pan angle
    setServoAngle(tilt_s,90) #baseline tilt angle
    while j < 1:
        #test default image
        ###take photo and process photo here
        Tomatoes_in_Image = mf.Process_Data(pipeline, align, aisle, plant)

	###
        
        i = 5 #dir ID
        if Tomatoes_in_Image != 0: #random_conf > confid_rating:
            break
        #setup base position
        #setServoAngle(pan_s,76)
        #setServoAngle(tilt_s,90)
        #f = open('tilt_up_test.txt')
        setServoAngle(pan_s,91) #pan right
        ###take photo and process photo here
        
        Tomatoes_in_Image = mf.Process_Data(pipeline, align, aisle, plant)

        ###
        i = 1
        if Tomatoes_in_Image !=0: #random_conf > confid_rating:
            break
        setServoAngle(pan_s,76) #recenter
        #setServoAngle(tilt_s,75) #tilt down
        ###take photo and process photo here
        
        #Tomatoes_in_Image = mf.Process_Data(pipeline, align, Aisle_Count, Plant_Number)

        ###
        #i = 2
        #if Tomatoes_in_Image !=0: #random_conf > confid_rating:
         #   break
        setServoAngle(tilt_s,90) #Recenter
        setServoAngle(pan_s,61) #pan left
        ###take photo and process photo here
        
        Tomatoes_in_Image = mf.Process_Data(pipeline, align, aisle, plant)

        ###
        i = 3
        if Tomatoes_in_Image !=0: #random_conf > confid_rating:
            break
        setServoAngle(pan_s,76) #recenter
        setServoAngle(tilt_s,75) #tilt up
        ###take photo and process photo here
        
        Tomatoes_in_Image = mf.Process_Data(pipeline, align, aisle, plant)

        ###
        i = 4
        if Tomatoes_in_Image !=0: #random_conf > confid_rating:
            break
        #Recenter
        j += 1
        #break
    if j ==1 :
        print(f"No tomatoes in view")
    elif i == 1:
        print(f"Pan right has tomatoes in view")
    elif i == 2:
        print(f"Tilt down has tomatoes in view")
    elif i == 3:
        print(f"Pan left has tomatoes in view")
    elif i == 4:
        print(f"Tilt up has tomatoes in view")
        #print(toc-tic)
    elif i == 5:
        print(f"Default image has tomatoes in view")
        #print(toc-tic)
    else:
        print("Max confidence reached")


def back_it_up():
    GPIO.output(15,GPIO.LOW) #enable turned on
    delay = 0.0000000001 #delay for the created pwm
    GPIO.output(13,GPIO.HIGH) #direction chosen: HIGH=CCW, LOW=CW

    print("\nMast moving downward\n") #start
    tic = int(time.perf_counter()) #timer start
    tac = 0.0 #total elapsed time initialized
    while tac < 20.0: #loop to run for 24 seconds
        GPIO.output(11, GPIO.HIGH) #step off
        sleep(delay)
        GPIO.output(11, GPIO.LOW) #step on
        sleep(delay)
        toc = int(time.perf_counter()) #timer end
        tac = toc - tic #total time elapsed 
        #print(tac)
    
    print(tac)
    print("\Plant scan is complete\n")

#Daltons Code for Servo Control
def Main_Dalton(aisle, plant):
    k = 0 #number of stops per plant
    setup()  
    GPIO.output(15,GPIO.LOW) #enable turned on
    delay = 0.0000000001 #delay for the created pwm
    GPIO.output(13,GPIO.LOW) #direction chosen: HIGH=CCW, LOW=CW
    #starter()
    while(k<2):
        shawty(aisle, plant)
        k+=1
    back_it_up()
    
def The_Whole_Enchilada():
    global Aisle_Count
    global Plant_Number
    
    while(Plant_Number<3):
        CF.Navigation_Main()
        Main_Dalton(Aisle_Count, Plant_Number)
        Plant_Number+=1
        print("You are currently on plant # ", Plant_Number)
    # After traveling the row, in this case 4 plants, the rover will navigate to the next aisle over
    Aisle_Count+=1
    print("You are now on Ailse # ", Aisle_Count)
    if Aisle_Count==2: #if on the last aisle [3] the code finishes
        print("\nFinished with greenhouse! WHOOP\n")
    else:
        Plant_Number=1
        CF.Travel_to_next_Aisle()
        The_Whole_Enchilada()

The_Whole_Enchilada()
pipeline.stop()
mf.Export_Log_to_Database()
print(f'\n\n\nEnd of run!!!\n\n\n')
