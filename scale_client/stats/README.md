SCALE statistics
====

This package contains some basic helper functions/scripts for parsing SensedEvent outputs and computing simple statistics from them e.g. % events received, latency, etc.
It uses the Python *pandas* library to collect the stats into an in-memory `DataFrame` object, which is similar to a relational database and allows similar operations on it. 

Caveats
----

The timestamp of SensedEvents will be inconsistent across devices so the time/latency-related computations are more effective if all the hosts are on the same node.
For example, you might run multiple SCALE clients on Mininet-based hosts to ensure they're using the same system clock.
Alternatively, do a round-trip measurement i.e. send events to a remote node for processing and have it report back the results (e.g. higher-level event) to the original node so you have a consistent clock.