#!/usr/bin/env python

from distutils.core import setup

setup(name='scale_client',
      version='0.2',
      description='Safe Community Awareness and Alerting Network (SCALE) client',
      author='Kyle Benson',
      author_email='kebenson@uci.edu',
      url='https://github.com/KyleBenson/SmartAmericaSensors',
      packages=['scale_client', 'scale_client.core',
                'scale_client.sensors', 'scale_client.event_sinks'],
      requires=['circuits', 'pyserial',
                'mosquitto',
                # TODO: how to only require this on a pi?
                # 'spidev',
                ]
      )

#TODO: replace mosquitto with paho?