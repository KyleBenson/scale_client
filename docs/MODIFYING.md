# Extending and modifying

SCALE is designed to be modified or extended by anyone with minimal Python programming abilities.

## Adding new classes

See the base classes for the following SCALE components in order to extend the system by deriving these classes to add new functionalities:

* Application
* VirtualSensor
* EventSink

You can also extend existing derive classes to modify their functionality slightly or leverage some of the existing code infrastructure.  For example, see the `GPIOVirtualSensor` or `AnalogVirtualSensor` classes and how their derived classes leverage common functionality.

NOTE: SCALE expects all classes instantiated and run by the core to accept `**kwargs` (keyword arguments) in their constructor (e.g. `__init__(arg1, arg2=3, ..., **kwargs)`).  Make sure to specify these and document them in your classes so that they can be properly passed in from the confugartion file.

NOTE: As SCALE is designed in a highly object-oriented manner, ensure that you properly defer to `super` when necessary wherever you override a method in order to properly handle inheritance.  In particular, you will need to do this with `__init__` (i.e. pass `**kwargs`) as well as methods such as `on_start()`.

## Architectural overview
TODO: expand and include diagram

SCALE is built around the concept of loosely-coupled components interacting via a pub-sub broker that handles exchanging `SensedEvent`s and other messages between the source that creates them and the interested entities that subscribe to them.

`SensedEvent`s represent the core data object, containing the raw data and associated metadata representing a sensor reading.
