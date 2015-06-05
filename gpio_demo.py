import sys
sys.path.append('library/python')

import serial
import marionette_lib
import struct
import pdb
from time import sleep

TTY = '/dev/ttyACM0'
TTY1 = '/dev/ttyACM0'

port = ['h', 'h', 'f', 'f', 'f', 'f', 'f', 'g',
        'g', 'e', 'e', 'e', 'e', 'e', 'e', 'e']

pin = ['5', '2', '12', '11', '14', '13', '15', '8',
       '1', '7', '9', '8', '11', '10', '12', '13']

OUTPUT = 'output_pushpull'

if __name__== "__main__":
    
    #Open Marionette connection and create object
    dut = marionette_lib.Marionette()
    try:
        dut.open(TTY)
    except OSError:
        dut.open(TTY1)
    
    status = dut.is_open()

    #Reset GPIO because we dont know current state
    try:
        for x in range(0, len(port)):
            dut.fetch_gpio_reset(port[x], pin[x])
    except marionette_lib.MarionetteResultError:
        next    
    for x in range(0, len(port)):
        dut.fetch_gpio_config(port[x], pin[x], OUTPUT)

    for x in range(0, 4):
        for x in range(0, len(port)):
            dut.fetch_gpio_set(port[x], pin[x])
            sleep(.25)

        for x in range(0, len(port)):
            dut.fetch_gpio_clear(port[x], pin[x])
            sleep(.25)

    for x in range(0, len(port)):
            dut.fetch_gpio_reset(port[x], pin[x])
