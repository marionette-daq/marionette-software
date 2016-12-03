import serial, threading, logging, time, ast

# disbales outputting log data to console by default
logging.getLogger(__name__).addHandler(logging.NullHandler())

SERIAL_READ_TIMEOUT = 3.0

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


class Marionette(object):
  def __init__(self, port=None, auto_open=True ):
    """
    Initialize marionette instance

    port = serial port

    """
    self._serial_port = port
    self._pyserial = None

    self.fetch = FetchROOT(self)
    self.gpio = FetchGPIO(self)
    self.i2c = FetchI2C(self)
    self.spi = FetchSPI(self)
    self.mbus = FetchMBUS(self)
    self.serial = FetchSERIAL(self)
    self.adc = FetchADC(self)
    self.dac = FetchDAC(self)
    self.mcard = FetchMCARD(self)
    self.mpipe = FetchMPIPE(self)

    if port and auto_open:
      self.open(port)

  def open(self, port=None):
    """
    Open marionette serial connection

    port = serial port
    """
    if self.is_open():
      raise MarionetteIOError("already open")

    if port:
      self._serial_port = port

    self._pyserial = serial.Serial(port=self._serial_port, timeout=SERIAL_READ_TIMEOUT)

    # setup for a non interactive shell
    self._pyserial.write("\r\n")
    self._pyserial.write("+noecho\r\n")
    self._pyserial.write("+noprompt\r\n")
    self._pyserial.write("\r\n")
    time.sleep(0.1)
    self._pyserial.flushInput()

  def close(self):
    if self._pyserial:
      self._pyserial.close()
      self._pyserial = None

  def is_open(self):
    if self._pyserial:
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
    if not self._pyserial:
      raise MarionetteIOError("serial port not open")

    logger = logging.getLogger(__name__)

    self._pyserial.flushInput()

    logger.debug("%r", fmt.strip() % args)

    self._pyserial.write(fmt.strip() % args)
    self._pyserial.write("\r\n")

    begin_flag = False
    results = {}
    error_list = []

    while True:
      line = self._pyserial.readline()

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
      elif param[0] in ('#', '?', 'w'): # info/debug/warning
        # these are all debug level messages at the python logging level
        logger.debug(":".join(param))
      elif param[0] == "e": # error
        error_str = ":".join(param[1:])
        error_list.append(error_str)
        logger.error(error_str)
      elif param[0] == "b" and len(param) == 3: # bool
        results[param[1]] = param[2].lower().strip() in ('true', 't', '1')
      elif param[0] == "s" and len(param) == 3: # string
        results[param[1]] = param[2]
      elif param[0] == "sa" and len(param) == 3: # string array
        results[param[1]] = param[2].split(',')
      elif param[0] == "se" and len(param) == 3: # string escape
        results[param[1]] = ast.literal_eval('"' + param[2] + '"')
      elif param[0] == "f" and len(param) == 3: # float
        results[param[1]] = map(float, param[2].split(','))
      elif param[0] in ("s8","u8","s16","u16","s32","u32") and len(param) == 3: # integer
        results[param[1]] = map(int, param[2].split(','))
      elif param[0] in ("h8","h16","h32") and len(param) == 3: # hex integer
        results[param[1]] = map(lambda x: int(x,16), param[2].split(','))
      else:
        raise MarionetteFormatError("invalid line format")

  def hex_str(self, data_list):
    output = bytearray()
    for data in data_list:
      if isinstance(data, list):
        output += bytearray(data)
      elif isinstance(data, (str,unicode)):
        output += bytearray(data)
      elif isinstance(data, bytearray):
        output += data
      elif isinstance(data, (int,long)):
        if data < 0 or data > 255:
          raise ValueError("invalid byte int")
        else:
          output += bytearray([data])
      else:
        raise TypeError("unable to convert to bytearray")
    return "h" + "".join(map(lambda x: "%02X" % x,output))

class FetchCommands():
  def __init__(self, marionette):
    if not isinstance(marionette, Marionette):
      raise TypeError(marionette)
    self.m = marionette

class FetchROOT(FetchCommands):
  def version(self):
    """ Query fetch version string """
    return self.m.command("version")

  def chip_id(self):
    """ Return marionette unique chip id as three 32bit integers """
    return self.m.command("chipid")["chip_id"]

  def reset(self):
    self.m.command("reset")

  def clocks(self):
    self.m.command("clocks")


class FetchGPIO(FetchCommands):
  def reset(self):
    self.m.command("gpio.reset")

  def read(self, *pins):
    return self.m.command("gpio.read(%s)" % ",".join(pins))

  def read_pin(self, *pins):
    return self.m.command("gpio.read(%s)" % ",".join(pins))

  def read_latch(self, *pins):
    return self.m.command("gpio.read_latch(%s)" % ",".join(pins))

  def read_port(self, port):
    return self.m.command("gpio.read_port(%s)" % port)

  def read_port_latch(self, port):
    return self.m.command("gpio.read_latch(%s)" % port)

  def read_all(self):
    return self.m.command("gpio.read_all")

  def write(self, pin, value):
    value = 1 if value else 0
    self.m.command("gpio.write(%s,%s)" % (pin, value))

  def write_many(self, *pin_value):
    pv_list = []
    for pv in pin_value:
      if not isinstance(pv, (tuple,list)):
        raise TypeError(pin_value)
      else:
        pin = pv[0]
        value = 1 if pv[1] else 0
        pv_list += "%s,%s" % (pin, value)
    self.m.command("gpio.write(%s)" % ",".join(pv_list))

  def write_port(self, port, value):
    self.m.command("gpio.write_port(%s,%s)" % (port,value))

  def write_all(self, val_a, val_b, val_c, val_d, val_e, val_f, val_g, val_h, val_i):
    self.m.command("gpio.write_all(%s,%s,%s,%s,%s,%s,%s,%s,%s)" % (val_a, val_b, val_c, val_d, val_e, val_f, val_g, val_h, val_i))

  def set(self, *pins):
    self.m.command("gpio.set(%s)" % ",".join(pins))

  def clear(self, *pins):
    self.m.command("gpio.clear(%s)" % ",".join(pins))

  def config(self, pin, mode, pull=None, otype='pushpull', ospeed=3):
    self.m.command("gpio.config(%s,%s,%s,%s, %s)" % (pin, mode, pull, otype, ospeed))

  def info(self, pin):
    return self.m.command("gpio.info(%s)" % pin)

  def shiftout(self, io_pin, clk_pin, rate, bits, *data):
    hex_data = self.m.hex_str(data)
    self.m.command("gpio.shiftout(%s,%s,%s,%s,%s)" % (io_pin, clk_pin, rate, bits, hex_data))

class FetchSPI(FetchCommands):
  def reset(self, dev):
    self.m.command("spi.reset(%s)" % dev)

  def clock_div(self):
    return self.m.command("spi.clock_div")

  def config(self, dev, cpol, cpha, clock_div, byte_order):
    self.m.command("spi.config(%s,%s,%s,%s,%s)" % (dev, cpol, cpha, clock_div, byte_order))

  def exchange(self, dev, cs_pin, cs_pol, *data):
    hex_data = self.m.hex_str(data)
    return self.m.command("spi.exchange(%s,%s,%s,%s)" % (dev, cs_pin, cs_pol, hex_data))

class FetchI2C(FetchCommands):
  def reset(self):
    self.m.command("i2c.reset")

  def config(self):
    self.m.command("i2c.config")

  def read(self, address, count):
    return self.m.command("i2c.read(%s,%s)" % (address, count))

  def write(self, address, *data):
    hex_data = self.m.hex_str(data)
    self.m.command("i2c.write(%s,%s)" % (address, hex_data))

class FetchMBUS(FetchCommands):
  pass

class FetchADC(FetchCommands):
  def reset(self):
    self.m.command("adc.reset")

  def start(self, dev):
    self.m.command("adc.start(%s)" % dev)

  def stop(self, dev):
    self.m.command("adc.stop(%s)" % dev)

  def single(self, dev):
    return self.m.command("adc.single(%s)" % dev)

  def config(self, dev, sample_rate):
    return self.m.command("adc.config(%s,%s)" % (dev, sample_rate))

  def status(self):
    return self.m.command("adc.status")

class FetchMCARD(FetchCommands):
  pass

class FetchMPIPE(FetchCommands):
  pass

class FetchDAC(FetchCommands):
  def reset(self):
    self.m.command("dac.reset")

  def write(self, channel, value):
    self.m.command("dac.write(%s,%s)" % (channel, value))

class FetchSERIAL(FetchCommands):
  def reset(self, dev):
    self.m.command("serial.reset(%s)" % dev)

  def config(self, dev, rate, hwfc):
    self.m.command("serial.config(%s,%s,%s)" % (dev, rate, hwfc))

  def set_timeout(self, tx_ms, rx_ms):
    self.m.command("serial.tiemout(%s,%s)" % (tx_ms, rx_ms))

  def get_timeout(self):
    return self.m.command("serial.timeout")

  def status(self, dev):
    return self.m.command("serial.status(%s)" % dev)

  def send_break(self, dev, time_ms):
    self.m.command("serial.break(%s,%s)" % (dev, time_ms))

  def read(self, dev, count):
    return self.m.command("serial.read(%s,%s)" % (dev, count))

  def write(self, dev, *data):
    hex_data = self.m.hex_str(data)
    self.m.command("serial.write(%s,%s)" % (dev, hex_data))
















