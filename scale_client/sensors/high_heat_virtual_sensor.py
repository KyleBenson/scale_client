from scale_client.sensors.virtual_sensor import VirtualSensor
from scale_client.core.sensed_event import SensedEvent

import logging
log = logging.getLogger(__name__)


class HighHeatVirtualSensor(VirtualSensor):

    def get_type(self):
        return "high_heat"

    def on_event(self, event, topic):
        threshold = 24.5
        if event.data['event'] == 'temperature' and event.data['value'] > threshold:
            self.publish(SensedEvent("high heat sensor",
                                     {"event": "high_heat",
                                      "value": "HOT!",
                                      'condition': {
                                          "threshold": {
                                              "operator": ">",
                                              "value": threshold
                                          }
                                      }
                                     }, 10))


    def policy_check(self, event):
        return False
