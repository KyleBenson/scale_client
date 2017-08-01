# Extending and modifying

SCALE is designed to be modified or extended by anyone with minimal Python programming abilities.  Please take a look at the [Architecture Documentation](ARCHITECTURE.md) first to understand how the system works.


## Adding New Classes

See the base classes for the following SCALE components in order to extend the system by deriving these classes to add new functionalities:

* Application
* VirtualSensor
* EventSink

You can also extend existing derived classes to modify their functionality slightly or leverage some of the existing code infrastructure.  For example, see the `GPIOVirtualSensor` or `AnalogVirtualSensor` classes and how their derived classes leverage common functionality.

After adding the new class make sure you enable it either via command line or the configuration file.


### Supporting SCALE's Inheritance Model

SCALE expects all classes instantiated and run by the core to accept `**kwargs` (keyword arguments) in their constructor (e.g. `__init__(arg1, arg2=3, ..., **kwargs)`).  Make sure to specify these and document them in your classes so that they can be properly passed in from the confugartion file.
 Note that the only positional argument (i.e. *args) your classes should accept is the `broker` argument that all children of `Application` accept.  This convention prevents placing such an argument in the wrong position and also ensures that users of your class can explicitly configure it using either the command line or configuration files as described in the [Configuring documentation](CONFIGURING.md).

As SCALE is designed in a highly object-oriented manner, ensure that you properly defer to `super` when necessary wherever you override a method in order to properly handle inheritance.  In particular, you will need to do this with `__init__` (i.e. pass `**kwargs`) as well as methods such as `on_start()`.


### Protocol-specific Formatting in EventSinks

Note that the `EventSink` class has a function called `encode_event()`.  You may need to overwrite this in order to format your `SensedEvent`s in a particular manner.  For example, our `SigfoxEventSink` needed to assign a well-known `SensedEvent` type to one of a few codes in order to transmit the event in the small message size supported by SigFox's ultra-narrowband technology.


### Using Threaded Applications/VirtualSensors

You may need to run long blocking operations in your new class, in which case you should consider deriving from the `ThreadedApplication` or `ThreadedVirtualSensor` class.  This ensures that your class runs in its own thread and won't block the others.
Note that we use explicit inheritance here rather than e.g. a keyword argument to enable threading because different runtime environments may need to handle threading differently than others.  By being explicit about when your class needs a thread to perform blocking operations, the scale client can ensure this guarantee while optimizing operations that may complete more quickly.


### Testing with Dummy Sensors

When you add a new `PhysicalSensor` class to support a new piece of directly-attached sensing hardware, you may wish to test other `Application`s that use this data without having to physically operate on the sensor to get certain readings.  You may also wish to run multiple scale clients exporting this data type but only have a single sensor.  In this case, you can make use of the `DummyPhysicalSensor` class to create your own dummy class like those found in the `sensors.dummy` module.  By subclassing `DummyPhysicalSensor` as well as your new `PhysicalSensor` implementation, you are explicitly telling the scale client that this test class does not actually manage a piece of hardware and so should not be treated like a device driver.  This has no major benefits currently but may affect platform optimizations in the future.


## Integrating New Protocols and Data Formats

A new data exchange protocol (e.g. DDS) can be added by creating a new `VirtualSensor` for receiving data or a new `EventSink` for sending data out.  For an example, see how we integrated CoAP as a new IoT protocol in addition to the original choice of MQTT.

Currently, `SensedEvent`s are all assumed to be transmitted/stored in the JSON format.  This feature is somewhat hard-coded into the client codebase by having the default implementation of `EventSink.encode_event(ev)` simply call `ev.to_json()`.  You likely should to handle new data formats at the `EventSink` by modifying this call as your system would need to coordinate which format to use with the receiving entity.


## Using a Different Pub-sub Backend or Python Framework

You may choose to integrate a different driving technology that implements the base funcionality of the `Application` class (i.e. its `run`, `publish`, and `subscribe` methods).  Doing so should ideally be as easy as implementing new `Broker` and `Application` classes to re-write the underlying logic.  However, you may have to modify the threading model in e.g. `ThreadedApplication` as well as perhaps make some slight changes to the `ScaleClient` in order to properly set up and run your framework.  There may be a few other implmentation-specific hacks floating around despite our best efforts to keep everything general.


## Adding New SensedEvent Types

This is currently unsupported as we handle all of the formatting and typing of events within the internal members, i.e. there is only a single `SensedEvent` type.  Expect this to potentially change in the future...
