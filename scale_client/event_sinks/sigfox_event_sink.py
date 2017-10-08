## 1. Install python serial package, details can be found at http://pyserial.sourceforge.net/pyserial.html#installation
## 2. Change the permission of your device, using "chmod o+rw". In my machine, it is "sudo chmod o+rw /dev/ttyUSB0"

import logging
log = logging.getLogger(__name__)

from scale_client.event_sinks.event_sink import EventSink
from scale_client.core.application import handler
import serial
import json
import os
import time

from circuits.core.timers import Timer
from circuits.core.events import Event

# TODO: do this using timed_call() instead
class SigfoxCheckEventSent(Event):
    """Signals the SigfoxEventSink to check whether the event was successfully sent."""


class SigfoxEventSink(EventSink):
    def __init__(self, broker,
                serialport='/dev/ttyUSB0',
                _baudrate=9600,
                _parity=serial.PARITY_NONE,
                _stopbits=serial.STOPBITS_ONE,
                _bytesize=serial.EIGHTBITS,
                **kwargs):
        super(SigfoxEventSink, self).__init__(broker, **kwargs)
        self._event_type_json_file = "sigfox_event_types.json"

        # Read from event type enum definition file (in JSON format)
        dirname, filename = os.path.split(os.path.abspath(__file__))
        log.debug(dirname)
        type_file = open(dirname + "/" + self._event_type_json_file, "rt")
        type_stream = type_file.read()
        self._type_info = json.loads(type_stream)

        self._serialport = serialport;
        self._baudrate = _baudrate;
        self._parity = _parity;
        self._stopbits = _stopbits;
        self._bytesize = _bytesize;

        self.__is_available = False
        self._ser = None
        self._reconnect_timer = None
        self._reconnect_timeout = 10

    def _try_connect(self):
        if self._ser is None:
            try:
                self._ser = serial.Serial(
                        port=self._serialport,
                        baudrate=self._baudrate,
                        parity=self._parity,
                        stopbits=self._stopbits,
                        bytesize=self._bytesize
                    )
            except serial.SerialException:
                pass
        if self._ser is None:
            log.error("Sigfox adapter not connected")
            self._reconnect_timer = time.time()
            return False
        if not self._ser.isOpen():
            self._ser.open()
        log.info("Sigfox adapter connected")
        self.__is_available = True
        self._reconnect_timer = None
        return True

    def check_available(self, event):
        if not event.event_type in self._type_info or not super(SigfoxEventSink, self).check_available(event):
            return False
        if self._ser is None or not self._ser.isOpen():
            if self._reconnect_timer is None or self._reconnect_timer + self._reconnect_timeout < time.time():
                self._try_connect()
        return self.__is_available

    def _ex_handler(self, obj):
        template = "An exception of type {0} occured. Arguments:\n{1!r}"
        message = template.format(type(obj).__name__, obj.args)
        log.error(message)

    def on_start(self):
        super(SigfoxEventSink, self).on_start()
        self._try_connect()

    def send_raw(self, encoded_event):
        #TODO: should define false code to indicate different fault reason
        if encoded_event is False:
            return False
        try:
            #self._ser.write(topic+"||"+msg+'\r\n')
            # Use the above paras to send actual sensor data

            self._ser.write(encoded_event)
        except serial.SerialException:
            log.error("Sigfox adaper writing failure")
            self._ser = None
            self.__is_available = False
            return False
        except Exception as err:
            self._ex_handler(err)
            return False

        log.info("Sigfox message: " + encoded_event.rstrip())
        self.__is_available = False
        # Check that message was sent ok after a timeout (no way to check that it was received!)
        self.set_event_check_timer()

    def set_event_check_timer(self, time_to_wait=7):
        """
        Sets a timer so that the SigfoxEventSink will check whether the event was successfully sent after the given
        time interval has expired.
        :param time: a number of seconds to wait or a datetime object representing when the check should be done
        """
        try:
            self._check_timer.reset(time_to_wait)
            self._check_timer.register(self)
            log.debug("Timer reset")
        except AttributeError:
            self._check_timer = Timer(time_to_wait, SigfoxCheckEventSent())
            self._check_timer.register(self)
            log.debug("Timer created")

    @handler("SigfoxCheckEventSent")
    def check_event_sent(self):
        #TODO: do this asynchronously so we don't always wait 7 seconds?
        ret = self.receive()
        if ret == 0:
            self.__is_available = True
        elif ret == -1:
            log.error("Unable to receive() reply from Sigfox adapter. Resetting timer...")
            self.set_event_check_timer()
        elif ret == -4: # IndexError
            self.__is_available = True
        elif ret == -7: # IOError
            self._ser = None
            self.__is_available = False

    def receive(self):
        # Read message from the sigfox adapter
        ret = ''  # Return message read

        try:
            while self._ser.inWaiting() > 0:
                ret += self._ser.read(1)
        except IOError:
            log.error("Sigfox adaper reading failure")
            return -7
        ret_strings = ret.split('\r\n')
        log.debug("Read from Sigfox adapter: " + ret)
        try:
            if ret_strings[1] == "OK":
                log.info("Sigfox message sent")
                return 0
            else:
                log.warning("Sigfox message not sent: " + ret_strings[1])
                return -1
        except IndexError:
            log.error("Index error when dealing with Sigfox return")
            return -4

    def encode_event(self, event):
        import ctypes

        log.debug("Encoding event: %s" % json.dumps(event.data))

        # The structure of Sigfox message:
        #  at$ss="payload_part"

            # The payload part of Sigfox message have following rules:
            # 1. Each payload character should be Hex character (0-F), which represent half byte.
            # 2. No more than 12 bytes (24 Hex characters)
            # 3. The message should be byte aligned, which means there should be even Hex characters

        hex_payload = " "

        # The structure of Sigfox message payload:
        #   Event Type (1 Byte/ 2 Hex Characters)
        # + Value Descriptor (2 Bytes / 4 Hex Characters) #TODO: Need More Work to Define
        # + Value (8 Bytes / 16 Hex Characters)
        # + Priority (4 bits / 1 Hex Characters)
        # + Control (Reserve bits)(4bits / 1 Hex Characters)


        # 1. Encode Event Type
        event_type_original = event.event_type

        try:
            event_type_encoded = self._type_info[event_type_original]
        except KeyError:
            log.warning("Unknown event: " + event_type_original)
            return False
        hex_payload_type = event_type_encoded

        # 2. Encode Value Descriptor
        # Temporary method
        hex_payload_vd = ""
        for i in range(4):
            hex_payload_vd += "0"

        # 3. Encode Value
        # Temporary method, just encode one float to first 4 bytes. Use for temperature data
        value_original = event.data

        if type(value_original) == type(9.0): # Handle float value
            hex_payload_value = hex(ctypes.c_int.from_buffer(ctypes.c_float(value_original)).value)[2:].zfill(8)
            #for i in range(8):
            #    hex_payload_value += "0"
            hex_payload_value += "0" * 8
        elif type(value_original) == type(9): # Handle int value
            hex_payload_value = hex(ctypes.c_int(value_original).value)[2:].zfill(4)
            hex_payload_value += "0" * 12
        else:
            #for i in range(16):
            #    hex_payload_value += "0"
            hex_payload_value = "0" * 16

        # 4. Encode Priority
        priority_original = event.priority
        if priority_original < 0 or priority_original > 15:
            log.warning("Priority value out of range")

        hex_payload_priority = hex(priority_original)[2] #[0:1] = '0x'

        # 5. Encode Control bits
        hex_payload_cb = "0"

        # 6. Generate Whole Hex Payload
        hex_payload = hex_payload_type + hex_payload_vd + hex_payload_value + hex_payload_priority + hex_payload_cb

        # Publish message "||" can be redefined. but '\r\n' is mandatory
        encoded_event = "at$ss=" + hex_payload + "\r\n"
        log.debug("Sigfox encoded: " + str(encoded_event).rstrip())
        return str(encoded_event)
