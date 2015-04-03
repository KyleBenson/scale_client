#!/usr/bin/env python

import socket
from distutils.core import setup

NAME = "scale_client"
VERSION = "0.2"
DESC = "Safe Community Awareness and Alerting Network (SCALE) client"
AUTHOR = "Kyle Benson"
AUTHOR_EMAIL = "kebenson@uci.edu"
URL = "https://github.com/KyleBenson/SmartAmericaSensors"
PACKAGES = ["scale_client", "scale_client.core",
            "scale_client.sensors", "scale_client.event_sinks"]
PACKAGE_DATA = {"scale_client": ["config/default_config.yml"]}
DATA_FILES = [("/etc/init.d", ["scripts/scale_daemon"])]

setup(name = NAME,
      version = VERSION,
      description = DESC,
      author = AUTHOR,
      author_email = AUTHOR_EMAIL,
      url = URL,
      packages = PACKAGES,
      package_data = PACKAGE_DATA,
      data_files = DATA_FILES,
      requires = ['circuits', 'pyserial',
                  'mosquitto',
                  # TODO: how to only require this on a pi?
                  # 'spidev',
                 ]
      )

