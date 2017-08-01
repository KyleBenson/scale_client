import time
from virtual_sensor import VirtualSensor
from ..core.threaded_application import ThreadedApplication

import logging
log = logging.getLogger(__name__)

class ThreadedVirtualSensor(VirtualSensor, ThreadedApplication):
    """
    Does its sensor reading in a background loop instead of using
    the repeat feature of Application.timed_call()
    """
    def __init__(self, broker, **kwargs):
        super(ThreadedVirtualSensor, self).__init__(broker=broker, **kwargs)
        self._sensor_thread_running = False

    def __sensor_loop(self, interval):
        """
        Simply loops until the sensor stops, reading sensor data every
        interval seconds.  Note that because this class is designed
        for long-running sensor reads that run best in background threads,
         it makes an effort to actually ensure the interval is followed
        by checking how long the actual sensor read took and adjusting
         the sleep time accordingly.
        :param interval:
        :return:
        """
        while self._sensor_thread_running:
            t1 = time.time()
            self._do_sensor_read()
            time_delta = time.time() - t1
            # log.debug("_do_sensor_read took %f secs to complete" % time_delta)
            sleep_time = interval - time_delta
            if sleep_time < 0:
                log.warning("_do_sensor_read took longer than interval time (%fs) to finish."
                            "  Not sleeping in attempt to catch up..." % interval)
            else:
                # log.debug("%s sleeping for %f seconds" % (self.__class__.__name__, sleep_time))
                time.sleep(sleep_time)

    def on_start(self):
        """
        Like VirtualSensor, this makes the sensor repeatedly call _do_sensor_read()
        every self.interval seconds.  The difference is that this version executes
        in a background thread and waits for the next read using time.sleep() rather
        than using a periodic timer.
        :return:
        """
        self._sensor_thread_running = True
        self.run_in_background(self.__sensor_loop, self._sample_interval)

    def on_stop(self):
        self._sensor_thread_running = False
        super(ThreadedVirtualSensor, self).on_stop()