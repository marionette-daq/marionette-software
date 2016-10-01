import sys
sys.path.append("../library/python/")
import marionette_lib as ml

if len(sys.argv) > 1:
  port = sys.argv[1]
else:
  port = "/dev/ttyACM0"

m = ml.Marionette(port)

# set voltage to 12bit max on first port of external dac
m.fetch_dac_write(1, 0xfff)

# set voltage on stm dac output to 0v
m.fetch_dac_write(4, 0)

