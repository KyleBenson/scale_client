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


#####    THESE WENT IN client.py    ######

# NOTE: in case we ever want to handle ctrl+c differently, here's a code snippet to do that with circuits:
#
# This ended up not being an actual bug but was related to a coapthon bug...
# Ensure that ctrl+c will also quit properly!
# XXX: circuits seems to set its own signal handler that fires a Signal Event and then calls stop(),
# but the current version fails to call Manager.stop() so we do so manually as a patch...  see circuits #234
# NOTE: this seems to be a bug related only to the fact that coapthon is creating its own threads and then
# calling back into the circuits library as this doesn't manifest when the CoapVirtualSensor isn't running.
# def __quit_signal_handler(signo, stack_frame):
#     self.__broker.__class__._signal_handler(self.__broker, signo, stack_frame)
#     self.__broker.stop()
# self.__broker._signal_handler = __quit_signal_handler



# Was using this to figure out what threads were still running when the client fails to exit...
# import threading
# print list(threading.enumerate())

# XXX: However, this seems to not always quit everything properly and sometimes results in
# hanging after quitting.  So we just force exit as a HACK instead...
# BUG: this seems to be due to something coapthon is doing with firing up additional threads,
# but I haven't investigated it fully other than to notice that it seems to only happen
# when the CoapVirtualSensor is running...

# This should normally do it, but since it seems to hang even with the main thread
# raise SystemExit(0)
# XXX: it REALLY doesn't want to quit...
# os._exit(0)
