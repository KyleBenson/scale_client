SCALE Client
=============

The Safe Community Awareness and Alerting Network (SCALE) project leverages the client code in this repo: a generic Python package designed for monitoring sensor devices, performing local processing on this data, and publishing results to a (possibly cloud-based) data exchange for further use. Use this package as a quick method to efficiently and flexibly set up a sensing platform (usually on a Raspberry Pi) that incorporates multiple sensors, actuators, networking technologies, and/or protocols.

Quickstart
----------

Clone the Git repo, ensure the current directory (`./`) is in your `PYTHONPATH`, install dependencies, and run the client from inside the main repo top-level directory.  This will run the default client configuration, which should print logging info to the console related to the dummy `VirtualSensor`s enabled by the default configuration file (see [Configuring](#configuring) for details).

For ease of reference, run all the following:

```bash
cd ~
git clone https://github.com/KyleBenson/scale_client.git
pip install -r requirements.txt
python -m scale_client --config ~/scale_client/scale_client/core/dummy_config.yml \
--log-level info
```

Installation
------------

For easy installation, simply run `sudo python setup.py install` from inside the main directory. Assuming you have `setuptools` installed via `pip`, this should handle installing all of the dependencies. Note that the codebase should run fine on any machine supporting Python 2.7+, but that it is tested on a Raspberry Pi running Raspbian and on Linux/Mac OSX machines (note that the latter won't support most physical sensor devices!). You don't **need** to run with `sudo`; doing so will install the daemon file.

If you don't wish to install the package and instead run it straight from the repository (as shown above in the Quickstart section), you can do so as long as the directory containing `scale_client` is in your `PYTHONPATH` or in the current directory.

The `scripts` directory contains some useful scripts for e.g. setting up the devices, running a daemon, etc.

Running
-------

You can run the code with `python -m scale_client` or `scale_client/core/client.py` as long as you set it up properly (i.e. your PYTHONPATH is set correctly and/or the Python package has been installed).

Documentation
===============

To aid others in leveraging the SCALE project for their own IoT deployments, we documented the SCALE codebase, devices, and deployment methodology.

included instructions for building your own SCALE devices (e.g. Raspberry Pi-based multi-sensor multi-network boxes).

## Source Code

This repository contains all of the SCALE client Python code that drives the individual IoT devices.  The flexible nature of these devices allows them to include a lot of intelligence or as little as you want.  We are currently working towards consolidating the SCALE client and server code so as to share as much event processing logic as possible between them.

### Directory structure

```
.
+-- scale_client: contains main Python package
|   +-- config: various example configuration files to run the client in different pre-set ways
|   +-- core: core client logic, abstract base classes, etc.
|       +-- client.py: driving main Python file for client
|       +-- sensed_event.py: abstract representation of a sensor reading, higher-level event, action, etc.
|       +-- event_reporter.py: handles the multiple EventSinks to upload (publish) SensedEvents that should be shared externally through the appropriate channel(s)
|   +-- sensors: all physical sensor interface wrappers and VirtualSensors reside here, subdivided into different categories
|   +-- applications: non-VirtualSensor applications that run various long-lived, analytics, or management-related operations live here
|   +-- event_sinks: implementations for the various EventSinks
|   +-- network: all modular networking-related functionality resides here
|   +-- test: simplistic test files to verify the client is working
+-- docs: additional documentation about SCALE client architecture, configuring, extending, etc.
+-- scripts: various installation scripts for different platforms
|   +-- scale_daemon: daemon script for running as a service
+-- csn_bin: contains binary files needed to integrate CSN sensor code for SCALE (not publicly supported or recommended)
+-- setup.py: installation script for default configuration/platform (NOTE: 2 other file versions for different configurations)
+-- requirements.txt: contains all Python pip requirements, some of which are commented out as they are only necessary for certain configurations
``` 


### Branches

The master branch has all the code you will likely use.  If you wish to experiment with our (currently unsupported) mesh networking functionality, the andy_mesh_network branch has extensions for using the BATMAN mobile ad-hoc protocol, but this branch is no longer up-to-date with our latest changes.


### Other Repositories

A notable fork of scale_client is [Qiuxi's repository for SCALECycle](https://github.com/bfrggit/scale_client) (look at the *cycle* branch).

The [original SCALE server repo](https://github.com/KyleBenson/SmartAmericaServer) contains a Python Django web app-based analytics and alerting service.  It requires some significant manual configuration and is no longer supported as we plan to migrate the logic in that repository to this one.  This consolidation will allow us to demonstrate and experiment with running analytics logic at various locations of the SCALE pipeline (i.e. on devices, in-network, in local vs. edge cloud servers, etc.).

The [ScaleSaltConfig repo](https://github.com/KyleBenson/ScaleSaltConfig) contains configuration files and dependencies used to remotely manage and provision SCALE devices automatically.  Note that it may be out of date from our latest iterations as we found it easier to simply clone Raspbian images with all the configuration already done when making several SCALE boxes of the same configuration.


## Building a SCALE Box

For directions on how to build your own SCALE devices (including hardware purchase list, assembly, and running SCALE on a Raspberry Pi with Raspbian), see our [evolving Google document](https://docs.google.com/document/d/1ItlumBB18bXcpRVaTrf4ghyYh6sCyd7HAMygooi9z8k/edit?usp=sharing).



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


Contributing
================

Please feel free to fork this repo for your own IoT research and development.  If you've fixed a significant bug or wish for SCALE to incorporate a new feature you added, please submit a pull request.  Your code should fit the same style and properly implement the SCALE Client architecture described in the documentation.

History
================

[SCALE](http://smartamerica.org/teams/scale-safe-community-alert-network-a-k-a-public-safety-for-smart-communities/) was originally envisioned as a demonstration of using the Internet of Things (IoT) for public and personal in-home safety applications as a response to the [SmartAmerica Challenge](http://smartamerica.org/) in 2014.  It has since evolved to include many different partnerships, organizations, and technologies.  Thus, it demonstrates a generic IoT project's organic evolution over time.

You can view the [SCALE project's website](http://scale.ics.uci.edu/) for additional information, publications, and a demonstration of the event-viewing dashboard.


Acknowledgements
================

Special thanks to the NSF; the University of California, Irvine; Montgomery County, MD; for sponsoring and supporting the SCALE project.  Additional thanks to the many other partners involved in SCALE!

Special thanks to the main SCALE software contributors:
* Kyle Benson
* Guoxi Wang
* Qiuxi Zhu

Licensing
================

See [LICENSE.txt file](LICENSE.txt) for official (permissive and business/open source friendly) licensing.