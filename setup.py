#!/usr/bin/env python

from distutils.core import setup

with open('requirements.txt') as F:
    requirements = [l.strip() for l in F.readlines() if not l.startswith("#")]

setup(name='scale_client',
      version='0.2',
      description='Safe Community Awareness and Alerting Network (SCALE) client',
      author='Kyle Benson',
      author_email='kebenson@uci.edu',
      url='https://github.com/KyleBenson/SmartAmericaSensors',
      packages=['scale_client', 'scale_client.core',
                'scale_client.sensors', 'scale_client.event_sinks'],
      requires=requirements,
      )
