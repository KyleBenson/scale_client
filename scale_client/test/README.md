Testing
=======

This folder contains a few Python scripts that are intended as a rudimentary testing suite.  We use Python's unittest where possible, but since a lot of the scale client is multi-threaded and reliant on networking, we instead prefer to run the actual client with the `--test` argument to validate that dummy sensor data gets published internally to various applications and reported in a simple `EventSink`.

For more complicated tests, including networked apps / database connections / physical sensing hardware, testing tends to be more manual.  It usually takes the form of running a configuration that publishes data to a remote `EventSink` and verifying that sink receives it e.g. by subscribing to it in a different client process.


TODO list
---------

The following are test suites that we plan to add eventually:

* virtual_sensors - unit testing some configuration parameters e.g. event_type changes the published event's type, sync vs. async mode work properly
* uri - should test the URI path creation/parsing mechanisms as well as any eventual URI registry service
* mysql - test that the database sink works properly
* raspi_sensors - test that the various physical sensors we've implemented to run on the Raspberry Pi function properly (NOTE: this could perhaps be done 95% of the way using Python's *mock* package to patch the GPIO/Analog sensor classes in order to have them return actual values).


### SCALE Client `core/client.py` unit tests

We also plan to add a whole test suite specifically for the core client module.  This will test the following currently-deemed-functional operations:

* ensure creating an app with no name (anonymous) works
* ensure we can set the app's name through either config file arg or cmd line arg
* ensure merging cmd line with config file(s) works
* ensure merging multiple config files works properly
* test loading classes not in the scale_client package directory
* regression tests for ensuring the client quits properly and doesn't hang due to e.g. threading problems

BUGFIXES that need to be resolved and then tested:

* not running Applications that built with errors (currently they still get ran by circuits since they weren't unregistered)