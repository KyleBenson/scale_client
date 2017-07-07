# Configuring the SCALE Client

This section assumes that you have already somewhat familiarised yourself with the [SCALE Client Architecture](ARCHITECTURE.md).  You may wish to do so first in order to understand the options available for you to configure.

## Main Command line arguments
```
--config FILENAME

--log-level [debug|info|warning|error]
```

Note that you can run the client with `-h` to view all available options, which include the ability to manually configure sensors, applications, and event_sinks as if they were written in the configuration file as described below.


## Configuration file
Configuration files are written in the [YAML](http://www.yaml.org/start.html) data serialization language.
See examples in the `scale_client/config` directory especially the [example configuration file that documents the various options available](../scale_client/config/example_config.yml).
The different possible sections in a configuration file mostly correspond to packages in the `scale_client` directory.
Each section may contain any number of entries, each of which express configurations used by the main `ScaleClient` thread of execution
to start up some module.
The currently possible sections are the following:

* `Main` - Configures aspects of the SCALE core, including the pub-sub broker, device or platform-specific information, networking, and event reporting policies.
* `EventSinks` - Enable and configure `EventSink`s, which provide methods for handling the reporting of `SensedEvent`s to a data exchange or other entity.
* `Sensors` - The real heart of SCALE, each class here represents a connection to some physical or virtual sensor and the configuration parameters that drive this connection and how it creates `SensedEvent`s.
* `Applications` - Applications represent entities that subscribe to certain sensor data feeds and may publish new events as a result.  The only real difference from `Sensors` is that they don't automatically perform a `read()` periodically.
* `Networks` - Currently unused but is reserved for networking-related configurations.

Note that each section (other than `Main`) lists the configurations for a number of Python classes.  The core system will try to create an instance of each listed class and run it within the SCALE environment on startup.  Of particular importance are the class names, which are resolved either relative to the topmost directory or to the corresponding directory within `scale_client` (e.g. `scale_client/sensors` for `Sensors`).  The remaining arguments for each class are passed directly to the class's constructor as `**kwargs`, so ensure you include all necessary ones, spell them properly, and verify that the value is legitimate or it may create an error during runtime.  SCALE tries to fail gracefully by logging these errors and not starting up the class in question when one occurs, and so it is your responsibility to enable logging during testing and verify that the classes are configured and run properly.


## Location for machine-specific configuration file

The SCALE daemon as a system service will always try to load `/etc/scale/client/config.yml` on start-up for a machine-specific configuration file. If it fails, it will try to load one of the default configuration files that comes with the package.

The setup script `setup.py` will create the directory `/etc/scale/client` recursively and put an example configuration file `example-config.yml` inside. Your machine-specific configuration file will NOT be overwritten during setup.
