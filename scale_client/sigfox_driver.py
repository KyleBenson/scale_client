##1. install python serial package, details can be found at http://pyserial.sourceforge.net/pyserial.html#installation
##2. change the permission of your device, using "chmod o+rw". In my machine, it is "sudo chmod o+rw /dev/ttyUSB0"


from sigfox_publisher import SIGFOXPublisher
from sensed_event import SensedEvent
import serial
import time

sig=SIGFOXPublisher("pre","suf")

if(sig.connect('/dev/ttyUSB0',
               9600,
               serial.PARITY_NONE,
               serial.STOPBITS_ONE,
               serial.EIGHTBITS)):
    event=SensedEvent("SampleSensor", "SampleMSG", 1)
    sig.send(event)
    time.sleep(1)
    print(sig.receive())
else:
    exit
