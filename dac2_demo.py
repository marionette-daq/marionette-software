import sys
sys.path.append('library/python')

import serial
import marionette_lib
import struct
import pdb
from time import sleep
from math import pi, sin, log, exp
TTY = '/dev/ttyACM0'
TTY1 = '/dev/ttyACM0'
def sweep(f_start, f_end, interval, n_steps, n_oversample=1):
    b = log(f_end/f_start) / interval
    a = 2 * pi * f_start / b
    for i in range(n_steps):
        for oversample in range(n_oversample):
            fractional_step = oversample / float(n_oversample)
            delta = (i + fractional_step) / float(n_steps)
            t = interval * delta
            g_t = a * exp(b * t)
            dut.fetch_dac_write(1, int(round(900 *(2 + sin(g_t)))))
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
    print("Device is open")
    try:
        dut.fetch_dac_reset(2)
        dut.fetch_dac_config(2)
        
    except marionette_lib.MarionetteResultError:
        pass
#    dut.fetch_dac_write(1, 3300)
#    sleep(5)
    dut.fetch_dac_write(2,3300)
    while True:
        for x in range(1, 3300):
           dut.fetch_dac_write(2, x)
          # sleep(.01)
        for x in range(3300, 1, -1):
            dut.fetch_dac_write(2, x)
           # sleep(.01)
