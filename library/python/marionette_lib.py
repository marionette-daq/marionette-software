import serial, threading, logging, time

# disbales outputting log data to console by default
logging.getLogger(__name__).addHandler(logging.NullHandler())

SERIAL_READ_TIMEOUT = 3.0

PORTA = 'a'
PORTB = 'b'
PORTC = 'c'
PORTD = 'd'
PORTE = 'e'
PORTF = 'f'
PORTG = 'g'
PORTH = 'h'
PORTI = 'i'

INPUT_FLOATING   = "input_floating"
INPUT_PULLUP     = "input_pullup"
INPUT_PULLDOWN   = "input_pulldown"
OUTPUT_OPENDRAIN = "output_opendrain"
OUTPUT_PUSHPULL  = "output_pushpull"

WAIT_HIGH    = "high"
WAIT_LOW     = "low"
WAIT_RISING  = "rising"
WAIT_FALLING = "falling"

class MarionetteError(Exception):
  pass

class MarionetteResultError(MarionetteError):
  pass

class MarionetteIOError(MarionetteError):
  pass

class MarionettePortPinError(MarionetteError):
  pass

class MarionettePortError(MarionettePortPinError):
  pass

class MarionettePinError(MarionettePortPinError):
  pass

class MarionetteFormatError(MarionetteError):
  pass


def check_port_pin(port,pin):
  if str(port).lower() not in ('a','b','c','d','e','f','g','h','i'):
    raise MarionettePortError("Invalid io port")
  try:
    if int(pin) not in range(16):
      raise MarionetteError()
  except (MarionetteError, ValueError):
    raise MarionettePinError("Invalid io pin")


class Marionette(object):
  def __init__(self, tty=None, auto_open=True ):
    """
    Initialize marionette instance

    tty = serial port

    """
    self.tty = tty
    self.serial = None

    if tty and auto_open:
      self.open(tty)

  def open(self, tty=None):
    """
    Open marionette serial connection

    tty = serial port
    """
    if self.is_open():
      raise MarionetteIOError("already open")

    if tty:
      self.tty = tty

    self.serial = serial.Serial(port=self.tty, timeout=SERIAL_READ_TIMEOUT)

    # setup for a non interactive shell
    self.serial.write("\r\n")
    self.serial.write("+noecho\r\n")
    self.serial.write("+noprompt\r\n")
    self.serial.write("\r\n")
    time.sleep(0.1)
    self.serial.flushInput()

  def close(self):
    if self.serial:
      self.serial.close()
      self.serial = None

  def is_open(self):
    if self.serial:
      return True
    else:
      return False

  def command(self, fmt, *args):
    """
    Issue a command to marionette and return its parsed response as a dictionary

    fmt   = command format string
    args  = optional arguments for positional substitution in fmt

    Returns a dictionary with name/value pairs for result data.

    If an error is returned from marionette a MarionetteResultError is raised with the error strings.

    Example:
    
    result = command("command(%s,%s)", arg1, arg2)

    is equivilent to
    
    result = command("command(%s,%s)" % (arg1, arg2))
    """
    if not self.serial:
      raise MarionetteIOError("serial port not open")
    
    logger = logging.getLogger(__name__)

    self.serial.flushInput()

    logger.debug("%r", fmt.strip() % args)

    self.serial.write(fmt.strip() % args)
    self.serial.write("\r\n")

    begin_flag = False
    results = {}
    error_list = []

    while True:
      line = self.serial.readline()

      logger.debug("%r", line)

      if line is None or len(line) == 0 or line[-1] not in "\r\n":
        raise MarionetteIOError("read timeout")

      param = line.lower().strip().split(":", 2)
      param[0] = param[0].lower()

      if param[0] == "begin":
        begin_flag = True
      elif not begin_flag:
        # ignore lines before first begin statement
        continue
      elif param[0] == "end" and len(param) == 2:
        if param[1].lower() == "ok" and len(error_list) == 0:
          return results
        elif param[1].lower() == "error":
          raise MarionetteResultError("\n".join(error_list))
        else:
          raise MarionetteFormatError("invalid end status")
      elif param[0] == "#": # info/comment
        logger.info(":".join(param[1:]))
      elif param[0] == "?": # debug
        logger.debug(":".join(param[1:]))
      elif param[0] == "e": # error
        error_str = ":".join(param[1:])
        error_list.append(error_str)
        logger.error(error_str)
      elif param[0] == "w": # warning
        logger.warning(":".join(param[1:]))
      elif param[0] == "b" and len(param) == 3: # bool
        results[param[1]] = param[2].lower().strip() in ('true', 't', '1')
      elif param[0] == "s" and len(param) == 3: # string
        results[param[1]] = param[2]
      elif param[0] == "sa" and len(param) == 3: # string array
        results[param[1]] = param[2].split(',')
      elif param[0] == "f" and len(param) == 3: # float
        results[param[1]] = map(float, param[2].split(','))
      elif param[0] in ("s8","u8","s16","u16","s32","u32") and len(param) == 3: # integer
        results[param[1]] = map(int, param[2].split(','))
      elif param[0] in ("h8","h16","h32") and len(param) == 3: # hex integer
        results[param[1]] = map(lambda x: int(x,16), param[2].split(','))
      else:
        raise MarionetteFormatError("invalid line format")


  # fetch commands

  def fetch_version(self):
    """ Query fetch version string """
    return self.command("version")

  def fetch_chip_id(self):
    """ Return marionette unique chip id as three 32bit integers """
    return self.command("chipid")["chip_id"]

  def fetch_reset(self):
    self.command("reset")

  # fetch gpio commands

  def fetch_gpio_read(self, port, pin):
    check_port_pin(port,pin)
    return self.command("gpio.read(%s,%s)", port, pin)["state"]

  def fetch_gpio_read_port(self, port):
    """ Read port state as 16 bit value """
    check_port_pin(port,0)
    return self.command("gpio.readport(%s)",port)["state"][0]

  def fetch_gpio_read_all(self):
    """ Read all ports as 16bit values """
    return self.command("gpio.readall")

  def fetch_gpio_write(self, port, pin, state):
    check_port_pin(port,pin)
    self.command("gpio.write(%s,%s,%s)", port, pin, bool(state))

  def fetch_gpio_set(self, port, pin):
    check_port_pin(port,pin)
    self.command("gpio.set(%s,%s)", port, pin)

  def fetch_gpio_clear(self, port, pin):
    check_port_pin(port,pin)
    self.command("gpio.clear(%s,%s)", port, pin)

  def fetch_gpio_config(self, port, pin, mode):
    """
    Configure pin as gpio

    mode = INPUT_FLOATING | INPUT_PULLUP | INPUT_PULLDOWN |
           OUTPUT_OPENDRAIN | OUTPUT_PUSHPULL
    """
    check_port_pin(port,pin)
    self.command("gpio.config(%s,%s,%s)", port, pin, mode)

  def fetch_gpio_info(self, port, pin):
    """
    Query current pin info

    Returns a dictionary indicating the current assigment, 
    available assignments, and io mode.
    """
    check_port_pin(port,pin)
    return self.command("gpio.info(%s,%s)", port, pin)

  def fetch_gpio_reset(self, port, pin):
    check_port_pin(port,pin)
    self.command("gpio.reset(%s,%s)", port, pin)

  def fetch_gpio_wait(self, port, pin, event, timeout):
    """
    Wait for event on a gpio pin

    event   = WAIT_LOW | WAIT_HIGH | WAIT_RISING | WAIT_FALLING
    timeout = milliseconds

    Returns true if event occured, false if wait timeout.

    """
    check_port_pin(port,pin)
    return self.command("gpio.wait(%s,%s,%s,%s)", port, pin, event, timeout)['event']

  # fetch adc commands

  def fetch_adc_start(self):
    """ Start an adc conversion """
    self.command("adc.start")

  def fetch_adc_stop(self):
    """ Stop a currently running adc conversion """
    self.command("adc.stop")

  def fetch_adc_wait(self, timeout=10):
    """
    Wait for adc conversion to finish

    timeout = milliseconds

    Returns true if conversion has completed
    """
    return self.command("adc.wait(%s)", timeout)["ready"]

  def fetch_adc_status(self):
    """
    Query adc conversion status

    Returns true if conversion has completed
    """

    return self.command("adc.status")["ready"]

  def fetch_adc_samples(self):
    """
    Queries last set of raw adc samples

    Returns a dictionary with the start time, stop time, and list of samples
    """
    return self.command("adc.samples")

  def fetch_adc_config(self, dev, res, sample_clk, vref, count, channels):
    """
    Configure adc module

    dev = ADC1 | ADC2 | ADC3
    res = RES12 | RES10 | RES8 | RES6
    sample_clk = CLK3 | CLK15 | CLK28 | CLK56 | CLK84 | CLK112 | CLK144 | CLK480
    vref = millivolts
    count = sample count per channel
    channels = list of channel id's (CH0 ... CH15, SENSOR, VREFINT, VBAT)
    """

    self.command("adc.config(%s,%s,%s,%s,%s,%s)", dev, res, sample_clk, vref, count, ",".join(channels))

  def fetch_adc_reset(self):
    self.command("adc.reset")

  # fetch dac commands

  def fetch_dac_config(self):
    """ Configure dac module """
    self.command("dac.config")

  def fetch_dac_reset(self):
    self.command("dac.reset")

  def fetch_dac_write(self, channel_1, channel_2):
    """ Write dac raw 12 bit values """
    self.command("dac.write(%s,%s)", channel_1, channel_2)

  # fetch spi commands

  def fetch_spi_config(self, dev, clk_polarity, clk_phase, clk_div, bit_order, port, pin):
    """
    Configure spi module

    dev = 1 | 2 | 3
    clk_polarity = 0 | 1
    clk_phase = 0 | 1
    clk_div = 0 ... 7
    bit_order = 0 (msb) | 1 (lsb)
    port = chip select port or None
    pin = chip select pin or None

    If a chip select port/pin are configured it will be 
    asserted low durring every spi exchange.
    """
    if port is not None or pin is not None:
      check_port_pin(port,pin)

    self.command("spi.config(%s,%s,%s,%s,%s,%s,%s)", dev, clk_polarity, clk_phase, clk_div, bit_order, port, pin)

  def fetch_spi_reset(self, dev):
    self.command("spi.reset(%s)", dev)

  def fetch_spi_exchange(self, dev, tx_data):
    """
    Clock data out/in spi port

    tx_data = bytearray of data to send

    if tx_data is a string or list it will be converted to a bytearray.

    Returns an equal length bytearray for input data.
    """

    if isinstance(tx_data, list):
      tx_data = bytearray(tx_data)
    elif isinstance(tx_data, (str,unicode)):
      tx_data = bytearray(tx_data)
    elif isinstance(tx_data, bytearray):
      pass
    else:
      raise TypeError("tx_data")

    result = self.command("spi.exchange(%s,16,%s)", dev, ",".join(map(lambda d: "%x" % d, tx_data)))
    return bytearray(result['rx'])

  # fetch i2c commands

  def fetch_i2c_config(self, dev):
    """
    Configure i2c module

    dev = 1 | 2 | 3
    """
    self.command("i2c.config(%s)", dev)

  def fetch_i2c_reset(self, dev):
    self.command("i2c.reset(%s)", dev)

  def fetch_i2c_transmit(self, dev, address, tx_data):
    """
    Transmit data to a i2c slave

    address = 7bit slave address
    tx_data = bytearray of data to send

    if tx_data is a string or list it will be converted to a bytearray.
    """

    if isinstance(tx_data, list):
      tx_data = bytearray(tx_data)
    elif isinstance(tx_data, (str,unicode)):
      tx_data = bytearray(tx_data)
    elif isinstance(tx_data, bytearray):
      pass
    else:
      raise TypeError("tx_data")

    self.command("i2c.transmit(%s,%s,16,%s)", dev, address, ",".join(map(lambda d: "%x" % d, tx_data)))

  def fetch_i2c_receive(self, dev, address, count):
    """
    Transmit data to a i2c slave

    address = 7bit slave address
    count = number of bytes to receive
    """
    result = self.command("i2c.receive(%s,%s,%s)", dev, address, count)
    return bytearray(result['rx'])










