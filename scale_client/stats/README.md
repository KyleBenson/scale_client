SCALE statistics
====

This package contains some basic helper functions/scripts/classes for IoT data experiments.
These include:

* `parsed_sensed_events.py`: parses SensedEvent outputs and computes simple statistics from them e.g. % events received, latency, etc.
It uses the Python *pandas* library to collect the stats into an in-memory `DataFrame` object, which is similar to a relational database and allows similar operations on it.
* `sensed_event_generator.py`: generates random SensedEvents from a data stream (i.e. event topic, creation time, size of random data) that is generated from specified distributions.
This can be used to make a collection of random data or even the events published by a `DummyVirtualSensor` that generates random events from various probability distributions (see `scipy.stats`).

Caveats
----

The timestamp of SensedEvents will be inconsistent across devices so the time/latency-related computations are more effective if all the hosts are on the same node.
For example, you might run multiple SCALE clients on Mininet-based hosts to ensure they're using the same system clock.
Alternatively, do a round-trip measurement i.e. send events to a remote node for processing and have it report back the results (e.g. higher-level event) to the original node so you have a consistent clock.

Notes
-----

We incorporate separate tests here since a user may opt not to install the `stats/requirements.txt` dependencies, which include some rather heavyweight libraries such as `scipy`.

TODO
----

* `subscription_generator.py`: used for modelling the topic interests of many subscribers.
Also uses the `scipy.stats` random number generators.
