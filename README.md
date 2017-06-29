SCALE Client
=============

The Safe Community Awareness and Alerting Network (SCALE) was originally envisioned as a demonstration of using the Internet of Things (IoT) for public and personal in-home safety applications as a response to the SmartAmerica Challenge in 2014.  It has evolved into a generic Python package designed for monitoring sensor devices, performing local processing on this data, and publishing results to a (possibly cloud-based) data exchange for further use. Use this package as a quick method to efficiently and flexibly set up a sensing platform (usually on a Raspberry Pi).

Quickstart
----------

Clone the Git repo and run: `pip install -r requirements.txt; python -m scale_client` from inside the main repo directory

Installation
------------

For easy installation, simply run `sudo python setup.py install` from inside the main directory. Assuming you have `setuptools` installed via `pip`, this should handle installing all of the dependencies. Note that the codebase should run fine on any machine supporting Python 2.7+, but that it is tested on a Raspberry Pi running Raspbian and on Linux/Mac OSX machines (note that the latter won't support most physical sensor devices!). You don't **need** to run with `sudo`; doing so will install the daemon file.

If you don't wish to install the package and instead run it straight from the repository, you can do so as long as the directory containing `scale_client` is in your `PYTHONPATH` or in the current directory.

The `scripts` directory contains some useful scripts for e.g. setting up the devices, running a daemon, etc.

Running
-------

You can run the code with `python -m scale_client` or `scale_client/core/client.py` as long as you set it up properly.

Configuring
-----------

SCALE is designed to be highly flexible and easily configurable.

### Main Command line arguments
```
--config FILENAME

--log-level [debug|info|warning|error]
```
Note that you can run the client with `-h` to view all available options, which include the ability to manually configure sensors, applications, and event_sinks as if they were written in the configuration file as described below.


### Configuration file
Configuration files are written in the *YAML* language.  See examples in the `scale_client/config` directory. There are currently 4 different sections to the configuration file:

* `Main` - Configures aspects of the SCALE core, including the pub-sub broker, device or platform-specific information, networking, and event reporting policies.
* `EventSinks` - Enable and configure `EventSink`s, which provide methods for handling the reporting of `SensedEvent`s to a data exchange or other entity.
* `Sensors` - The real heart of SCALE, each class here represents a connection to some physical or virtual sensor and the configuration parameters that drive this connection and how it creates `SensedEvent`s.
* `Applications` - Applications represent entities that subscribe to certain sensor data feeds and may publish new events as a result.  The only real difference from `Sensors` is that they don't automatically perform a `read()` periodically.

Note that each section (other than `Main`) lists the configurations for a number of Python classes.  The core system will try to create an instance of each listed class and run it within the SCALE environment on startup.  Of particular importance are the class names, which are resolved either relative to the topmost directory or to the corresponding directory within `scale_client` (e.g. `scale_client/sensors` for `Sensors`).  The remaining arguments for each class are passed directly to the class's constructor as `**kwargs`, so ensure you include all necessary ones, spell them properly, and verify that the value is legitimate or it may create an error during runtime.  SCALE tries to fail gracefully by logging these errors and not starting up the class in question when one occurs, and so it is your responsibility to enable logging during testing and verify that the classes are configured and run properly.

### Location for machine-specific configuration file

The SCALE daemon as a system service will always try to load `/etc/scale/client/config.yml` on start-up for a machine-specific configuration file. If it fails, it will try to load one of the default configuration files that comes with the package.

The setup script `setup.py` will create the directory `/etc/scale/client` recursively and put an example configuration file `example-config.yml` inside. Your machine-specific configuration file will NOT be overwritten during setup.

Extending and modifying
-----------------------

SCALE is designed to be modified or extended by anyone with minimal Python programming abilities.

### Adding new classes

See the base classes for the following SCALE components in order to extend the system by deriving these classes to add new functionalities:

* Application
* VirtualSensor
* EventSink

You can also extend existing derive classes to modify their functionality slightly or leverage some of the existing code infrastructure.  For example, see the `GPIOVirtualSensor` or `AnalogVirtualSensor` classes and how their derived classes leverage common functionality.

NOTE: SCALE expects all classes instantiated and run by the core to accept `**kwargs` (keyword arguments) in their constructor (e.g. `__init__(arg1, arg2=3, ..., **kwargs)`).  Make sure to specify these and document them in your classes so that they can be properly passed in from the confugartion file.

NOTE: As SCALE is designed in a highly object-oriented manner, ensure that you properly defer to `super` when necessary wherever you override a method in order to properly handle inheritance.  In particular, you will need to do this with `__init__` (i.e. pass `**kwargs`) as well as methods such as `on_start()`.

### Architectural overview
TODO: expand and include diagram

SCALE is built around the concept of loosely-coupled components interacting via a pub-sub broker that handles exchanging `SensedEvent`s and other messages between the source that creates them and the interested entities that subscribe to them.

`SensedEvent`s represent the core data object, containing the raw data and associated metadata representing a sensor reading.

Acknowledgements
================

Special thanks to the NSF; the University of California, Irvine; Montgomery County, MD; for sponsoring and supporting the SCALE project.  Additional thanks to the many other partners involved in SCALE!

You can view the SCALE project's website at http://scale.ics.uci.edu/ for additional information, publications, and a demonstration of the event-viewing dashboard.

Licensing
================

Copyright (c) 2017, UC Irvine

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies,
either expressed or implied, of the FreeBSD Project.
