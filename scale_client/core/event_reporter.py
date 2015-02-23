from application import Application


class EventReporter(Application):
    """
    The EventReporter is a special-purpose Application that is the sole entity responsible
    for managing how SensedEvents are transferred to other locations in the network.  It
    does not directly call on network devices, sockets, etc. to transfer this data.
    Rather, it decides which SensedEvents to report when and then chooses from the
    available Publishers the ideal one to report the data via.
    """
    def __init__(self, queue):
        super(EventReporter, self).__init__(self)
        self._queue = queue
        self._ls_pb = []
        self._ls_queue = []

    def append_publisher(self, pb):
        self._ls_pb.append(pb)

    def send_false_callback(self, pb, event, false_reason):
        # TODO: Need to have a send fail dealing policy, Now we just discard
        print pb.get_name()+" send failed"
        return True

    def run(self):
        while True:
            event = self._queue.get()

            for pb_j in self._ls_pb:
                if pb_j.check_available(event):
                    pb_j.send(event)
