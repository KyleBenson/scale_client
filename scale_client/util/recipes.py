# This file contains code snippets that were used for hacking / debugging but were not necessarily
# important enough to keep around in the main code.


THREAD_CREATION_LOGGING = True
if THREAD_CREATION_LOGGING:
    import threading

# DEBUGGING: this hack finds the current threads, looks at them again
# after starting the Worker to find the set difference, and then prints
# out what threads were started for this process so we can figure out
# e.g. which ones are hanging.
if THREAD_CREATION_LOGGING:
    old_threads = set(str(i) for i in threading.enumerate())

# DO STUFF HERE

if THREAD_CREATION_LOGGING:
    new_threads = set(str(i) for i in threading.enumerate())
    log.debug(
        "Constructing %s created new threads: %s" % (self.__class__.__name__, '\n'.join(new_threads - old_threads)))
