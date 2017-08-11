Testing
=======

This folder contains a few Python scripts that are intended as a rudimentary testing suite.  We use Python's `unittest` where possible for both quick simple API tests (e.g. default construction parameters work) as well as longer *integration-style testing*.
Because a lot of the scale client is multi-threaded and reliant on networking, the integration-style tests (e.g. [test_coap.py](test_coap.py)) typically run several processes configured with statistics-gathering `EventSink`s and/or `Application`s.  The unit tests verify that the resulting stats gathered are as expected.  While this isn't a perfect solution, it does provide a more complete test framework for checking edge cases and preventing regressions than the older testing style.

The older style is simply to run the actual scale client with the `--test` argument and `--log-level debug` to visually and manually validate that sensor data gets published internally to various applications and reported in a simple `EventSink`.
We might have this data published to the MQTT broker so we can see it by subscribing in a different client process (e.g. the dashboard).
We still use this method for features that don't yet have unit tests as well as a first approximation of a functioning deployment (e.g. right packages installed, MQTT broker reachable).
It's especially helpful for more manual/physical tests, including networked apps / database connections / physical sensing hardware.


TODO list
---------

If you look in existing test suites, you may find some TODO comments about test cases that will be added later. 
The following are test suites that we plan to add eventually:

* application - unit testing for default path and properly setting default values in make_event
* virtual_sensors - unit testing some configuration parameters e.g. event_type changes the published event's type, sync vs. async mode work properly
* mysql - test that the database sink works properly
* raspi_sensors - test that the various physical sensors we've implemented to run on the Raspberry Pi function properly (NOTE: this could perhaps be done 95% of the way using Python's *mock* package to patch the GPIO/Analog sensor classes in order to have them return actual values).
* mqtt - verify that mqtt sink and sensor (not yet implemented) work properly, including recovery from disconnects
* event_reporter - test its event sinking policies, in particular ensuring that remote events aren't forwarded to sinks (this is partially tested in coap suite)
* internet_access - test the ability for the client to gracefully handle spotty internet access i.e. connection loss, re-established, lost again, etc.


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