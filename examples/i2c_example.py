import sys
sys.path.append("../library/python/")
import marionette_lib as ml

if len(sys.argv) > 1:
  port = sys.argv[1]
else:
  port = "/dev/ttyACM0"

m = ml.Marionette(port)

# make sure i2c pins are configured as i2c mode
m.fetch_i2c_config()

# write to i2c device
# first argument is the 7 bit address
# seconds argument is the number base to interpret bytes, reference strtoul
# following arguments are the bytes to send out, in this case the 4 bytes with values 0, 1, 2, 3
m.fetch_i2c_write(80, 0, 0, 1, 2, 3)

# read from i2c device
# first argument is the 7 bit address
# second argument is the number of bytes to read
result = m.fetch_i2c_read(80, 16)
print result

