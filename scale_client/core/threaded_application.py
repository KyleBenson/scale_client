from circuits.core.workers import Worker as CircuitsWorker
from circuits import handler
from circuits.core.workers import task
from scale_client.core.application import Application

import logging
log = logging.getLogger(__name__)


class Worker(CircuitsWorker):
    """
    This class is necessary to patch the circuits library, which will not
    properly terminate any running threads/processes when receiving SIGINT.
    The fix is to call pool.terminate() here so they exit immediately.
    """
    @handler("stopped", "unregistered", channel="*", override=True)
    def _on_stopped(self, event, *args):
        if event.name == "unregistered" and args[0] is not self:
            return
        self.pool.terminate()

class ThreadedApplication(Application):
    """
    Classic Applications are meant to run quick operations periodically
    or asynchronously.  Sometimes, it is much easier with or impossible
    without threads to perform blocking operations, busy wait, etc.  Use
    this class to accomplish such a use case by using this class's
    run_in_background(...) function.  You may consider binding 'self' into
    the args list so that you can run a method on the given instance.
    Just don't forget about thread safety!!
    """

    def __init__(self, broker, process=False, n_threads=1, **kwargs):
        """
        :param broker: the broker used for the internal pub-sub feature core to the scale_client
        :param process: True to use processes rather than Threads
        :param n_threads: Number of threads to start (default=1)
        :param kwargs: used for passing args to other constructors when doing multiple inheritance
        """
        super(ThreadedApplication, self).__init__(broker, **kwargs)
        self._worker = Worker(process=process, workers=n_threads,
                              # need to ensure only this worker receives
                              # tasks we fire
                              channel=self._get_channel_name())
        self._worker.register(self)

    def run_in_background(self, f, *args, **kwargs):
        """
        Runs the given function f in the background thread/process.
        Add args and kwargs to pass them to the function.
        """

        self._worker.fire(task(f, *args, **kwargs), self._get_channel_name())

    # def on_stop(self):
    #     """
    #     Clean up the threads/background processes we used.  Make sure you call this function in a derived class
    #     using super!
    #     :return:
    #     """
    #     # NOTE: this is already handled in the Worker wrapper class above!
    #     self._worker.pool.terminate()
    #     log.debug("threaded app STOPPED WORKER!")
    #     super(ThreadedApplication, self).on_stop()