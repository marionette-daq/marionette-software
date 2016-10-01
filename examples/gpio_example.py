import sys
sys.path.append("../library/python/")
import marionette_lib as ml

if len(sys.argv) > 1:
  port = sys.argv[1]
else:
  port = "/dev/ttyACM0"

m = ml.Marionette(port)

# many gpio commands require a port (A-I)  and pin (0-15) on the stm32
# Note: in the future this will change to be a single string parameter


# make sure pins are at a known default configuration
# for most pins this is input floating
m.fetch_gpio_reset()

# set pin PG0 to output
m.fetch_gpio_config('g', 0, 'OUTPUT_PUSHPULL')

# set pin to HIGH
m.fetch_gpio_write('g', 0, 1)

# set pin to LOW
m.fetch_gpio_write('g', 0, 0)

# alternate way of setting HIGH
m.fetch_gpio_set('g',0)

# alternate way of setting LOW
m.fetch_gpio_clear('g', 0)

# set PG1 to input with pullup
m.fetch_gpio_config('g', 1, 'INPUT_PULLUP')

# read pin state
result = m.fetch_gpio_read('g', 1)
print result


