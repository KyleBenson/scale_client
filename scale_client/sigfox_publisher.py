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
		self._ser=None

	def _ex_handler(self,obj):
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
			self._ser=serial.Serial(
				port=_port,
				baudrate=_baudrate,
				parity=_parity,
				stopbits=_stopbits,
				bytesize=_bytesize
			)
		except Exception as err: 
			self._ex_handler(err)
			return False

		if(not self._ser.isOpen()):
			self._ser.open()
		print("Sigfox adapter connected")
		return True

	def send(self, event):
		self._queue.put(event)

	def publish(self, coded_event):
		try:
			#self._ser.write(topic+"||"+msg+'\r\n')
			#use the above paras to send actual sensor data    
			self._ser.write(coded_event)
		except Exception as err: 
			self._ex_handler(err)
			return False
        
        # check that message was sent ok (no way to check that it was received!)
        	time.sleep(5)
        #TODO: fix this sleep interval so it doesn't block the whole event reporter
		return self.receive()

	def receive(self):
		#read message from the sigfox adapter
		ret='' #return message read
		while self._ser.inWaiting()>0:
			ret+=self._ser.read(1)
		print ("read from sigfox adapter: "+ret)
		ret_strings = ret.split('\r\n')
		if ret_strings[1] == "OK":
			return True
		else:
			return False	

	def encode_event(self,event):
		# Publish message "||" can be redefined. but '\r\n' is mandatory
		print event.msg
		hex_payload = "0fd1"
		coded_event = "at$ss=" + hex_payload + "\r\n"

		return coded_event

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
