#!/usr/bin/python2

import sys
import serial
import readline
from time import sleep

if len(sys.argv) < 2:
  print("Usage: %s <serial port>" % sys.argv[0])
  exit(1)

tty = serial.Serial(port=sys.argv[1],timeout=3)

# disable prompt and echo since we handle that localy with readline input
tty.write("\r\n")
tty.write("+noecho\r\n")
tty.write("+noprompt\r\n")
tty.write("\r\n")
sleep(0.2)
tty.flushInput()

try:
  while True:
    cmd = raw_input("m > ").strip()
    if len(cmd) == 0:
      continue # ignore blank lines

    # special local terminal commands
    # local commands except 'exit' will start with '-' (contrasting to mshell '+')
    if cmd == 'exit' or cmd == '-exit':
      print("Exiting")
      break
    elif cmd == '-reopen':
      print("Reopen serial port")
      tty.close()
      tty.open()
      continue
    elif cmd == '-help':
      print("Local terminal help (TODO)")
      continue

    tty.write(cmd + "\r\n")
    # read lines until we get an 'end' marker or we timeout
    line = tty.readline().rstrip('\r\n')
    while len(line) > 0:
      print(line)
      if line.lower().startswith("end:"):
        break
      else:
        line = tty.readline().rstrip('\r\n')

except KeyboardInterrupt:
  print("Exiting")
finally:
  tty.close()

