"""
Implements a conduit over a serial port.
"""

import logging
import re

from serial import Serial
from serial import serial_for_url
from serial.tools import list_ports

logger = logging.getLogger(__name__)

import serial
from serial.aio import SerialTransport
import asyncio
from asyncio import Queue
from serial.aio import create_serial_connection
from io import TextIOWrapper

LOGGER = logging.getLogger(__name__)

class SerialProtocol(asyncio.Protocol):
    def __init__(self):
        super(asyncio.Protocol, self).__init__()
        self._msg_queue = Queue()
        self._buffer = ""

    def connection_made(self, transport):
        self.transport = transport
        self.transport.serial.rts = False
        LOGGER.debug('port opened {0}'.format(transport))

    async def watch_messages(self):
        LOGGER.debug("watching message queue...")
        while True:
            yield await self._msg_queue.get()

    def data_received(self, data):
        self._buffer += data.decode()

        for line in self._coerce_message_from_buffer():
            LOGGER.debug("new full line: {0}".format(line))
            line = line.replace(' ', '')
            self._msg_queue.put_nowait(line.encode()) # FIXME: Make sure it's right


    def _coerce_message_from_buffer(self):
        """
        Try to make a message out of the buffer and find log messages intertwined
        into the buffer.
        """
        log_messages = []
        while '\n' in self._buffer:
            # stripped_buffer, log_messages = self._filter_out_log_messages(self.buffer)
            if len(log_messages) > 0:
                yield from log_messages
                self._buffer = stripped_buffer
                continue

            lines = self._buffer.partition('\n')  # returns 3-tuple with line, separator, rest
            if not lines[1]:
                # '\n' not found, first element is incomplete line
                self._buffer = lines[0]
            else:
                # complete line received, [0] is complete line [1] is separator [2] is the rest
                self._buffer = lines[2]
                yield lines[0].rstrip('\r').rstrip('\n')




    def connection_lost(self, exc):
        LOGGER.debug('port closed')
        asyncio.get_event_loop().stop()


class SerialConduit:
    """
    A Conduit for a Serial Port (using pyserial)
    """
    def __init__(self, port):
        self._loop = asyncio.get_event_loop()
        self.port = port
        self.transport = None
        self.serial = serial.Serial(port, baudrate=57600)
        self.protocol = SerialProtocol()

    def bind(self):
        # self.serial = Serial(self.port, baudrate=57600)
        self.transport = SerialTransport(self._loop, self.protocol, self.serial)
        return self.transport != None

    async def write(self, data):
        self.serial.write(data)

    async def watch_messages(self):
        yield await self.protocol.watch_messages()

    @property
    def is_bound(self):
        return self.serial.is_open


class SerialConduit2():
    """
    A conduit that provides comms via a serial port.
    """

    def __init__(self, ser: Serial):
        self.ser = ser

    @property
    def input(self):
        return self.ser

    @property
    def output(self):
        return self.ser

    @property
    def open(self) -> bool:
        return self.ser.isOpen()

    def close(self):
        self.ser.close()


def serial_ports():
    """
    Returns a generator for all available serial port device names.
    """
    for port in serial_port_info():
        yield port[0]


def serial_connector_factory(*args, **kwargs):
    """
    Creates a factory function that connects via the serial port.
    All arguments are passed directly to `serial.Serial`
    :return: a factory for serial connectors
    """

    def open_serial_connector():
        ser = Serial(*args, **kwargs)
        return SerialConduit(ser)

    return open_serial_connector


particle_devices = {
    (r"Spark Core.*Arduino.*", r"USB VID\:PID=1D50\:607D.*"): "Spark Core",
    (r".*Photon.*", r"USB VID\:PID=2d04\:c006.*"): "Particle Photon",
    (r".*P1.*", r"USB VID\:PID=2d04\:c008.*"): "Particle P1",
    (r".*Electron.*", r"USB VID\:PID=2d04\:c00a.*"): "Particle Electron"
}

known_devices = dict((k, v) for d in [particle_devices] for k, v in d.items())


def matches(text, regex):
    return re.match(regex, text)


def is_recognised_device(p):
    port, name, desc = p
    for d in known_devices.keys():
        # used to match on name and desc, but under linux only desc is
        # returned, compard
        if matches(desc, d[1]):
            return True  # to name and desc on windows
    return False


def find_recognised_device_ports(ports):
    for p in ports:
        if is_recognised_device(p):
            yield p[0]


def serial_port_info():
    """
    :return: a tuple of serial port info tuples,
    :rtype:
    """
    return tuple(list_ports.comports())


def detect_port(port):
    if port == "auto":
        all_ports = serial_port_info()
        ports = tuple(find_recognised_device_ports(all_ports))
        if not ports:
            raise ValueError(
                "Could not find arduino-compatible device in available ports. %s" % repr(all_ports))
        return ports[0]
    return port


# todo - this is an application property that apps can override where needed.
def configure_serial_for_device(s, d):
    """ configures the serial connection for the given device.
    :param s the Serial instance to configure
    :param d the device (port, name, details) to configure the serial port
    """
    # for now, all devices connect at 57600 baud with defaults for parity/stop
    # bits etc.
    s.setBaudrate(57600)


# class SerialWatchdog(ResourceWatchdog):
#     """ Monitors local serial ports for known devices. """

#     def check(self):
#         """ Re-evaluates the available serial ports. """
#         self.update_ports(tuple(serial_port_info()))

#     def is_allowed(self, key, device):
#         return super().is_allowed(key, device) and is_recognised_device(device)

#     def update_ports(self, all_ports):
#         """ computes the available serial port/device map from a list of tuples (port, name, desc). """
#         available = {p[0]: p for p in all_ports if self.is_allowed(
#             p[0], p) and is_recognised_device(p)}
#         self.update(available)
