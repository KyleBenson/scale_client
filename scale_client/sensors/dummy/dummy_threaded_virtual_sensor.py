from ..threaded_virtual_sensor import ThreadedVirtualSensor

class DummyThreadedVirtualSensor(ThreadedVirtualSensor):
    def read_raw(self):
        return "dummy_thread_reading"

    def get_type(self):
        return "dummy_thread"