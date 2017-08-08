from scale_client.core.application import Application
from scale_client.sensors.virtual_sensor import VirtualSensor
from scale_client.core.sensed_event import SensedEvent
from scale_client.event_sinks.log_event_sink import LogEventSink
from scale_client.core.event_reporter import EventReporter
from scale_client.sensors.dummy_temperature_virtual_sensor import DummyTemperatureVirtualSensor

# from circuits.core.handlers import handler
from scale_client.core.application import handler
from circuits.core.manager import Manager
from circuits.core.timers import Timer


class BombLit(SensedEvent):

    def __init__(self=None:
        SensedEvent.__init__("explosion_sensor", self, "psssssss!!", 4)


class Explosion(SensedEvent):
    """blahblah"""

    def __init__(self=None:
        SensedEvent.__init__("explosion_sensor", self, "BOOM!", 1)


class Fire(SensedEvent):
    def __init__(self=None:
        SensedEvent.__init__("fire_sensor", self, "Fire!", 2)


class Bomb(Application):

    def on_start(self):
        print "bomb is lit!"
        event = BombLit()
        self.publish(event)

        timer = Timer(1, BombLit(), persist=True)
        timer.register(self)

    @handler("Fire")
    def on_fire(self, event):
        print "OMG I STARTED A FIRE!!!"

    @handler("BombLit")
    def on_lit(self, event):
        print "bomb blew up!"
        self.publish(Explosion())


class SensorBomb(Bomb, VirtualSensor):

    def on_start(self):
        pass

    def read(self):
        print "lighting a bomb..."
        return BombLit()


class DudBomb(Bomb):
    """
    This class demonstrates overriding on_start to perform other actions.
    """
    def on_start(self):
        print "this is not a dud bomb!"
        super(DudBomb, self).on_start()


class Gasoline(Application):

    # def on_event(self, event, topic):
    #     print "event received!"

    @handler("Explosion")
    def on_bomb(self, event):
        print "the gasoline caught fire!"
        self.publish(Fire())


class FireAlarm(Application):

    def on_start(self):
        self.publish(SensedEvent("blah", "some sensor", 1))

    @handler("Fire")
    def on_fire(self, event):
        print "beep beep! FIRE!"
        self.publish(SensedEvent("fire alarm!", "fire sensor", 1))


class Logger(Application):

    # @handler("SensedEvent")
    def on_event(self, event, topic):
        print "new event:", event.__class__.__name__


def main():
    broker = Manager()
    alarm = FireAlarm(broker)

    # bomb = Bomb(broker)
    # bomb = DudBomb(broker)
    bomb = SensorBomb(broker)

    gas = Gasoline(broker)

    # logger = Logger(broker)
    logger = LogEventSink(broker)
    reporter = EventReporter(broker)
    reporter.add_sink(logger)

    DummyTemperatureVirtualSensor(broker)

    # alarm.subscribe(Fire)
    broker.run()

if __name__ == "__main__":
    main()