Sensors Module
========

The sensors module contains all of the functionality related to sensing.  In particular, it contains the base classes and various different enhancements that support physical sensing (readings from a physically attached sensor device) and virtual sensing (readings from remote devices or detected higher-level events).


PhysicalSensors
--------------

TODO: bring in the original VirtualSensor discussion to here from the docs?  maybe the docs could then include this README or at least link to it


VirtualSensors
---------

VirtualSensors take raw 'low-level' SensedEvents from the other PhysicalSensors, or perhaps other VirtualSensors, and analyze them to detect higher-level events for publishing.  Currently, these are basically just Applications for which you specify the events the VS consumes.  Implement the necessary analysis logic in on_event, package the data your VS publishes, and then export it using export_virtual_event in order to publish this new event with an audit trail that shows the original event(s) that lead to this new higher-level event.

# TODO: document the API


DummySensors
-----------

The dummy_sensors module contains classes intended for testing purposes.  Ideal for running on a laptop during development or anywhere for demonstrations and testing, these sensors report somewhat realistic-looking sensor readings without requiring a physical sensor device.

# TODO: document the generic_dummy_sensor module once we create it!


NetworkSensors
-------------

These sensors are designed for doing any sort of networking-related sensing, which might include not only gathering network state information/statistics but also reading sensed data from remote devices/services.  Possible examples  of the former include a simple ping for detecting if we have Internet access and scanning for nearby devices to form the mesh network.  Possible examples of the latter include pulling from remote RESTful APIs using CoAP or HTTP, subscribing to a remote MQTT broker's events, or receiving events through a BLE connection to an external sensing device.


Implementations
---------------

The various directories here contain our implementations for different sensors we integrated with the SCALE client.  Most of these are cheap off-the-shelf devices that were hooked directly to a Raspberry Pi.  You could easily sub-class them and change the sensor reading logic in order to keep the same data format but integrate them with a different physical sensor device.  As an example, see the usb_temperature_sensor.py module.

Note that we attempted to organize the various implementations by different types e.g. environmental, security, network, etc.