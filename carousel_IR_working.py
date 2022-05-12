import time
import keyboard
import numpy as np
from os import system, name
from pyfirmata2 import Arduino
from functions import *


sampling_rate = 100

PORT = Arduino.AUTODETECT
board = Arduino(PORT)
# board = Arduino("COM3") # for the MEG
board.samplingOn(1000 / sampling_rate)

ir_led_pin = board.get_pin("d:9:p")
ir_led_pin.write(True)
ir_rec_pin = board.get_pin("a:0:i")
ir_rec_pin.enable_reporting()

print("IR sensor test")
time.sleep(0.5)
while True:
    try:
        ir = ir_rec_pin.read()
        if ir != None:
            mpl = int(ir*100)
            print(":"+"|"*mpl)
        time.sleep(0.2)
    except KeyboardInterrupt:
        break


positions = {
    0 : [0, "pinch", 30],
    6  : [60, "palm", 30],
    12 : [120, "pinch", 60],
    18 : [180, "palm", 60],
    24 : [240, "pinch", 90],
    30 : [300, "palm", 90]
}


gpios = [3, 4, 5, 6]

time_step = 0.15

available_calib_pos = [0, 6, 12, 18, 24, 30]

pos = 0
valve = 0

pos, valve = calibration(pos, valve, available_calib_pos, ir_rec_pin, gpios, time_step, board)

while True:
    try:
        if keyboard.is_pressed("w"):
            pos, valve = forward(pos, valve)
            blow(gpios[valve], time_step, gpios, board)
            pd = ir_rec_pin.read()
            print("\n\n", pos, valve, pd)

        elif keyboard.is_pressed("s"):
            pos, valve = backward(pos, valve)
            blow(gpios[valve], time_step, gpios, board)
            pd = ir_rec_pin.read()
            print("\n\n", pos, valve, pd)

        elif keyboard.is_pressed("q"):
            while True:
                pos, valve = forward(pos, valve)
                blow(gpios[valve], time_step, gpios, board)
                pd = ir_rec_pin.read()
                print("\n\n", pos, valve, pd)
                if pos in list(positions.keys()):
                    break
        
        elif keyboard.is_pressed("a"):
            while True:
                pos, valve = backward(pos, valve)
                blow(gpios[valve], time_step, gpios, board)
                pd = ir_rec_pin.read()
                print("\n\n", pos, valve, pd)   
                if pos in list(positions.keys()):
                    break
        else:
            on(gpios[valve], board)
        
        pd = ir_rec_pin.read()
        if (pos in available_calib_pos) and (pd > 0.01):
            print("Calibration Required")
            # clear()
            pos, valve = calibration(pos, valve, available_calib_pos)

    except KeyboardInterrupt:
        break