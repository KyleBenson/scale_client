##1. install python serial package, details can be found at http://pyserial.sourceforge.net/pyserial.html#installation
##2. change the permission of your device, using "chmod o+rw". In my machine, it is "sudo chmod o+rw /dev/ttyUSB0"

from publisher import Publisher
from sensed_event import SensedEvent
from Queue import Queue
import time
import serial


class SigfoxPublisher(Publisher):
    def __init__(self, name, queue_size, callback):
        Publisher.__init__(self, name, queue_size, callback)
        self._ser = None
        self._event_type_json_file = "event_type.json"

    def _ex_handler(self, obj):
        template = "An exception of type {0} occured. Arguments:\n{1!r}"
        message = template.format(type(obj).__name__, obj.args)
        print message

    def connect(self,
                _port='/dev/ttyUSB0',
                _baudrate=9600,
                _parity=serial.PARITY_NONE,
                _stopbits=serial.STOPBITS_ONE,
                _bytesize=serial.EIGHTBITS):
        try:
            self._ser = serial.Serial(
                port=_port,
                baudrate=_baudrate,
                parity=_parity,
                stopbits=_stopbits,
                bytesize=_bytesize
            )
        except Exception as err:
            self._ex_handler(err)
            return False

        if (not self._ser.isOpen()):
            self._ser.open()
        print("Sigfox adapter connected")
        return True

    def send(self, event):
        self._queue.put(event)

    def publish(self, coded_event):
        #TODO: should define false code to indicate different fault reason
        #if coded_event is False:
        #    return False
        try:
            #self._ser.write(topic+"||"+msg+'\r\n')
            #use the above paras to send actual sensor data
            self._ser.write(coded_event)
        except Exception as err:
            self._ex_handler(err)
            return False

            # check that message was sent ok (no way to check that it was received!)
        time.sleep(7)
        #TODO: fix this sleep interval so it doesn't block the whole event reporter
        return self.receive()

    def receive(self):
        #read message from the sigfox adapter
        ret = ''  #return message read
        while self._ser.inWaiting() > 0:
            ret += self._ser.read(1)
        print ("read from sigfox adapter: " + ret)
        ret_strings = ret.split('\r\n')
        try:
            if ret_strings[1] == "OK":
                return True
            else:
                return False
        except IndexError:
            print "Index Error when dealing with Sigfox return "
            return False

    def encode_event(self, event):
        import json
        import ctypes
        import os
        print event.msg

        #The Structure of Sigfox message:
        #  at$ss="payload_part"

            #The payload part of Sigfox message have following rules:
            #1. Each payload character should be Hex character(0-F), which represent half byte.
            #2. No more than 12 bytes(24 Hex characters)
            #3. The message should be byte aligned, which means there should be even Hex characters

        hex_payload = " "

        #The Structure of Sigfox message payload:
        #   Event Type(1 Byte/ 2 Hex Characters)
        # + Value Descriptor(2 Bytes / 4 Hex Characters) #TODO: Need More Work to Define
        # + Value(8 Bytes / 16 Hex Characters)
        # + Priority(4 bits / 1 Hex Characters)
        # + Control(Reserve bits)(4bits / 1 Hex Characters)


        # 1. Encode Event Type
        event_type_original = event.msg["event"]

        # Read from Event Type Enum Definition File(in JSON format)
        dirname, filename = os.path.split(os.path.abspath(__file__))
        type_file = open(dirname+"/"+self._event_type_json_file, "rt")
        type_stream = type_file.read()
        type_info = json.loads(type_stream)

        try:
            event_type_encoded = type_info[event_type_original]
        except KeyError:
            print "Unknown Event: " + event_type_original
            return False
        hex_payload_type = event_type_encoded

        # 2. Encode Value Descriptor
        # Temporary method
        hex_payload_vd = ""
        for i in range(4):
            hex_payload_vd += "0"

        # 3. Encode Value
        # Temporary Method, just encode one float to first 4 bytes. Use for temperature data
        if hex_payload_type != "01" and hex_payload_type != "02":
            hex_payload_value = ""
            for i in range(16):
                hex_payload_value += "0"
        else:
            value_original = event.msg["value"]
            hex_payload_value = hex(ctypes.c_int.from_buffer(ctypes.c_float(value_original)).value)[2:]

            for i in range(8):
                hex_payload_value += "0"

        # 4. Encode Priority
        priority_original = event.priority
        if priority_original < 0 or priority_original > 15:
            print "Priority Value Out of Range"

        hex_payload_priority = hex(priority_original)[2] #[0:1] = '0x'

        # 5. Encode Control bits
        hex_payload_cb = "0"

        # 6. Generate Whole Hex Payload
        hex_payload = hex_payload_type + hex_payload_vd+ hex_payload_value + hex_payload_priority + hex_payload_cb

        # Publish message "||" can be redefined. but '\r\n' is mandatory
        coded_event = "at$ss=" + hex_payload + "\r\n"
        print "Sigfox Ready to Send: " + str(coded_event)
        return str(coded_event)

    def check_available(self, event):
        if self._queue.qsize() < (self._queue_size):
            return True
        else:
            return False


'''
	def run(self):
		while True:
			event = self._queue.get()	
			ret = self.publish(self.encode_event(event))	
			print "published: "
			if ret == False:
				self._queue.put(event)
'''
'''
#Debug use, run sigfoxpubisher independently
def main():
	sig=SigfoxPublisher()

	if(sig.connect()):
		event=SensedEvent("SampleSensor", "SampleMSG", 1)
		sig.send(event)#convert event to sigfox format here!
		ret_event = self._queue.get()
				ret = self.publish(self.encode_event(ret_event))
				if ret == False:
					self._queue.put(ret_event)
	else:
		exit

if __name__ == "__main__":
	main()
'''
