#!/usr/bin/env python

from distutils.core import setup

setup(name='scale_client',
      version='0.1',
      description='Safe Community Awareness and Alerting Network (SCALE) client',
      author='Kyle Benson',
      author_email='kebenson@uci.edu',
      url='https://github.com/KyleBenson/SmartAmericaSensors',
      packages=['scale_client', 'scale_client.core',
                'scale_client.sensors', 'scale_client.publishers'],
      )
