import time
import numpy as np
from os import system, name
from pyfirmata2 import Arduino
from functions import *


sampling_rate = 100

PORT = Arduino.AUTODETECT
# board = Arduino(PORT)
board = Arduino("COM3") # for the MEG
board.samplingOn(1000 / sampling_rate)

ir_led_pin = board.get_pin("d:11:p")
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
        else:
            print(ir)
        time.sleep(0.2)
    except KeyboardInterrupt:
        break

ir_led_pin.write(0)
ir_rec_pin.disable_reporting()