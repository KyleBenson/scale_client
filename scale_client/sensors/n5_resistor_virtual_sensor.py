from scale_client.sensors.analog_virtual_sensor import AnalogVirtualSensor

import logging
log = logging.getLogger(__name__)

class N5ResistorVirtualSensor(AnalogVirtualSensor):
	def __init__(self, broker, device=None, interval=1, analog_port=None):
		super(N5ResistorVirtualSensor, self).__init__(broker, device, interval, analog_port)

	DEFAULT_PRIORITY = 9

	VOLT_ADC = 5.0
	VOLT_ALL = 5.0
	RSST_STD = 10.0
	RSST_AIR = 10.0

	def read_raw(self):
		adcout = super(N5ResistorVirtualSensor, self).read_raw()
		adcmax = self.READ_MAX or self.HDWR_MAX
		volt_x = 1.0 * self.VOLT_ADC * adcout / adcmax
		rsst_s = (1.0 * self.VOLT_ALL / volt_x - 1) * self.RSST_STD
		return rsst_s / self.RSST_AIR

	def get_type(self):
        return "raw_n5_resistor"

    def policy_check(self, data):
        return True
