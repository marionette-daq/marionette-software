import sys
sys.path.append("../library/python/")
import marionette_lib as ml

if len(sys.argv) > 1:
  port = sys.argv[1]
else:
  port = "/dev/ttyACM0"

m = ml.Marionette(port)

# config command is needed to set sample rate for streaming mode
# single sample mode it is not needed and the defaults are fine

# configure adc2 sample rate
m.fetch_adc_config(2, 100)

# start streaming samples over mpipe
m.fetch_adc_start(2)

# stop streaming samples over mpipe
m.fetch_adc_stop(2)

# read a single sample
results = m.fetch_adc_single(2)
print results

