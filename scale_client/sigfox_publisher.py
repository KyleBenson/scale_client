from publisher import Publisher
from sensed_event import SensedEvent
import time
import serial 

class SIGFOXPublisher(Publisher):
	def __init__(self, topic_prefix, topic_suffix = ""):
		self._topic_prefix = topic_prefix
		self._topic_suffix = topic_suffix
		self._ser=None

	def _exHandler(self,obj):
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(obj).__name__, obj.args)
            print message

	def connect(self,p,b,pa,s,bs):
		try:
                            
                    self._ser=serial.Serial(
                    port=p,
                    baudrate=b,
                    parity=pa,
                    stopbits=s,
                    bytesize=bs)
                    
                except Exception as err: 
                    self._exHandler(err)
                    return False
		if(not self._ser.isOpen()):
                    self._ser.open()
		return True

	def send(self, event):
		# Make message from a sensed event
		topic = self._topic_prefix + "/" + event.sensor + "/" + self._topic_suffix
		msg = event.msg + " @" + str(event.timestamp)

		# Publish message "||" can be redefined. but '\r\n' is mandatory
		try:
                    #self._ser.write(topic+"||"+msg+'\r\n')
                    #use the above paras to send actual sensor data    
                    self._ser.write("AT"+'\r\n')
                except Exception as err: 
                    self._exHandler(err)
                    return False
                
		print "SigFox message published to " + topic
		return True
	def receive(self):
                #read message from the sigfox adapter
                ret='' #return message read
                while self._ser.inWaiting()>0:
                    ret+=self._ser.read(1)
                return ret
                    
            
