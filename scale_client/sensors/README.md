Sensors Module
========

The sensors module contains all of the functionality related to sensing whether it involves a physical sensing device, remote ones, or other forms of sensing such as receiving events over the network or pulling from web pages.


VirtualSensors
---------

VirtualSensors represent an abstract sensor data feed by obscuring and managing the details of where, how, and when a sensor reading is collected and packed into a SensedEvent to be published internally.
take raw 'low-level' SensedEvents from the other PhysicalSensors, or perhaps other VirtualSensors, and analyze them to detect higher-level events for publishing.  Currently, these are basically just Applications that can be run in two sensing modes: synchronous or asynchronous.

In **synchronous mode**, you start the sensor with an argument (see API) that sets the sampling rate.  Every *interval* seconds, it will read sensor data, pack it into a SensedEvent, and optionally publish it if it passes some policy_check.

In **asynchronous mode**, you specify the events the VS consumes and it calls on_event for each of them.  Implement the necessary analysis logic in on_event, package the data your VS publishes, and then export it by making a new event and calling publish.  You may wish to include in this new event an audit trail that shows the original event(s) that lead to this new higher-level event.

All VirtualSensors have some *data source*, which you may explicitly set during configuration (or directly in the class implementation).  This might be the physical device from which it is reading, the network connection it's using, or the events it subscribed to.  If unspecified, it tries to intelligently fill the field with something unique (see the API for updated details) such as the subscriptions or eventually the sensor_type().


PhysicalSensors
--------------

A PhysicalSensor is a VirtualSensor for which the programmer is essentially stating that their class will directly manage a physically-attached sensor device. As such, it can essentially be regarded as a sort of device driver that manages a specific hardware implementation. Note that a sensor device managed via a network connection such as BLE should not be implemented as a PhysicalSensor since another piece of software is handling the actual physical management of the sensor itself. Currently, the only difference is that it requires specifying a *device*, which will be used as the *data source*.  In the future, this could be used for certain local optimizations.


DummySensors
-----------

The dummy_sensors module contains classes intended for testing purposes.  Ideal for running on a laptop during development or anywhere for demonstrations and testing, these sensors report somewhat realistic-looking sensor readings without requiring a physical sensor device or network connection.

# TODO: document the generic_dummy_sensor module once we create it!


NetworkSensors
-------------

These sensors are designed for doing any sort of networking-related sensing, which might include not only gathering network state information/statistics but also reading sensed data from remote devices/services.  Possible examples  of the former include a simple ping for detecting if we have Internet access and scanning for nearby devices to form the mesh network.  Possible examples of the latter include pulling from remote RESTful APIs using CoAP or HTTP, subscribing to a remote MQTT broker's events, or receiving events through a BLE connection to an external sensing device.


Event-Detectors
---------------

These VirtualSensors explicitly represent a sensor feed that uses lower-level readings from PhysicalSensors, performs some event-detection analysis on them, and asynchronously publishes higher-level events.  They currently do not use a special class type for this purpose, but future implementations could make use of other libraries or platforms for e.g. handling streaming data.


Implementations
---------------

The various directories here contain our implementations for different sensors we integrated with the SCALE client.  Most of these are cheap off-the-shelf devices that were hooked directly to a Raspberry Pi.  You could easily sub-class them and change the sensor reading logic in order to keep the same data format but integrate them with a different physical sensor device.  As an example, see the usb_temperature_sensor.py module.

Note that we attempted to organize the various implementations by different types e.g. environmental, location, network, etc.  This is not necessarily a rigid classification and could be subject to change.  It is more of a guideline for collecting many different sensor implementations in a way that a human programmer or user can easily search the available catalog.
