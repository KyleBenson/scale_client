# Configuring the SCALE Client

This section assumes that you have already somewhat familiarised yourself with the [SCALE Client Architecture](ARCHITECTURE.md).  You may wish to do so first in order to understand the options available for you to configure.


## Main Command line arguments
```
--config FILENAME

--log-level [debug|info|warning|error]
```

Note that you can run the client with `-h` to view all available options, which include the ability to manually configure sensors, applications, and event_sinks as if they were written in the configuration file as described below.
Note also that these manual configurations can be used to overwrite or modify the configuration parameters specified in a configuration file.  For example, you may wish to change the sensor sampling rate or the IP address of the MQTT broker but keep the rest of the configurations intact.  See the help option for more details.


## Configuration file

Configuration files are written in the [YAML](http://www.yaml.org/start.html) data serialization language and structured mostly as nested dictionaries.
See examples in the `scale_client/config` directory especially the [example configuration file that documents the various options available](../scale_client/config/example_config.yml).
The different possible sections in a configuration file mostly correspond to packages in the `scale_client` directory.
Each section may contain any number of entries, each of which express configurations used by the main `ScaleClient` thread of execution
to start up some module.
The currently possible sections are the following:

* `Main` - Configures aspects of the SCALE core, including the pub-sub broker, device or platform-specific information, networking, and event reporting policies.
* `EventSinks` - Enable and configure `EventSink`s, which provide methods for handling the reporting of `SensedEvent`s to a data exchange or other entity.
* `Sensors` - The real heart of SCALE, each class here represents a connection to some physical or virtual sensor and the configuration parameters that drive this connection and how it creates `SensedEvent`s.
* `Applications` - Applications represent entities that subscribe to certain sensor data feeds and may publish new events as a result.  The only real difference from `Sensors` is that they don't automatically perform a `read()` periodically.
* `Networks` - This section runs `Application`s and any required support modules for networking-related configurations e.g. CoAP, detecting Internet access, mesh networking, etc.

Note that each section (other than `Main`) lists the configurations for a number of Python classes.  The core system will try to import and then create an instance of each listed class (see below) and run it within the SCALE environment on startup.
The heading for each entry (a YAML key for the dictionary that is the configuration) should be a unique human-readable name for the component being configured; it is passed as the `name` argument to the component's constructor (see below).

The remaining arguments for each class are passed directly to the class's constructor as `**kwargs`, so ensure you include all necessary ones, spell them properly, and verify that the value is legitimate or it may create an error during runtime.  SCALE tries to fail gracefully by logging these errors and not starting up the class in question when one occurs, and so it is your responsibility to enable logging during testing and verify that the classes are configured and run properly.


### Importing Classes by Path

Of particular importance are the `class` names, which are resolved either relative to the topmost directory or to the corresponding directory within `scale_client` (e.g. `scale_client/sensors` for `Sensors`).
The core system tries to *lazily import* these classes for each possible resolved location before finally showing an error message that the import was unsuccessful.
A key advantage of this *lazy import* strategy is that the client will start more quickly instead of waiting for all of the possible modules and their dependencies to be imported.
Another major advantage is that only the necessary dependencies and third-party modules for a particular deployment need be installed on the system; this prevents import errors related to an unneeded dependency or unavailable module (e.g. `VirtualSensor`).


### Importing multiple configuration files

The `Main` section supports a special option for combining multiple configuration files.  You can import these files in a manner that merges options whenever possible and overwrites the later (left-most) files by adding the following option:

`include_config_files: ["config_file_1.yml", "config2.yml"]`

See the example config file for more details.


### Location for machine-specific configuration file

The SCALE daemon as a system service will always try to load `/etc/scale/client/config.yml` on start-up for a machine-specific configuration file. If it fails, it will try to load one of the default configuration files that comes with the package.

The setup script `setup.py` will create the directory `/etc/scale/client` recursively and put an example configuration file `example-config.yml` inside. Your machine-specific configuration file will NOT be overwritten during setup.


## Configuring `Application`s and `VirtualSensor`s

While you should see the individual classes for a more detailed and complete list, the following parameters are some of the configuration options supported by most `Application`s and `VirtualSensor`s:

* `sample_interval` - the sensor will call `read()` and possibly publish an event every `sample_interval` seconds (this is synchronous mode).  You can also use the keyword `interval` for backwards compatibility with the older API.
* `subscriptions` - accepts a list of strings where each entry is the event topic (e.g. temperature) that this `Application` should subscribe to.  Every time such an event is published, the `Application`'s `on_event()` method will be called.  For a `VirtualSensor`, this is asynchronous mode.
* `advertisements` - list of topics this `Application` may publish to.  Note that the first one is used as the default `event_type` for created `SensedEvent`s.  The `event_type` parameter is available for `VirtualSensor`s and can set this first advertisement directly.
* `name` - a unique human-readable name for the configured object that defaults to its class name.  Note that the key for the whole object configuration is assumed as the default name; so you will overwrite that by specifying this parameter directly.  By default, not specifying a name (i.e. configuring via command-line option) will cause a random name to be generated, but if you create an `Application` instance directly without a name its class name will be used.
* `device` - this parameter, a URI string or simple name, for a `PhysicalSensor` is intercepted by the scale client and used to create a `DeviceDescriptor` that simply identifies the sensing device by its path and name.  It will be automatically generated from the object's `name` if unspecified.
* `threshold` - many of the `PhysicalSensor` implementations accept this parameter in order to only publish sensor readings when their raw data value exceeds `threshold`.  This parameter may eventually be incorporated into `VirtualSensor` so that all derived classes can make use of it.
