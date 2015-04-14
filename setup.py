#!/usr/bin/env python

from setuptools import setup

# Generic info about package
NAME = "scale_client"
VERSION = "0.2"
DESC = "Safe Community Awareness and Alerting Network (SCALE) client"
AUTHOR = "Kyle Benson"
AUTHOR_EMAIL = "kebenson@uci.edu"
URL = "https://github.com/KyleBenson/SmartAmericaSensors"

# Specific information about package contents
PACKAGES = ["scale_client", "scale_client.core",
            "scale_client.sensors", "scale_client.event_sinks"]
PACKAGE_DATA = {"scale_client": ["config/*"]}
DAEMON_LOCATION = "/etc/init.d"
DATA_FILES = [(DAEMON_LOCATION, ["scripts/scale_daemon"])]

# Gather requires info from requirements.txt
with open('requirements.txt') as F:
    requirements = [l.strip() for l in F.readlines() if not l.startswith("#")]

# Check whether we will be able to install the daemon or not
try:
    with open(DAEMON_LOCATION, 'w') as F:
        pass
except IOError:
    print "Can't access daemon location. Skipping daemon installation..."
    DATA_FILES = None

setup(name=NAME,
      version=VERSION,
      description=DESC,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=URL,
      #not needed in setuptools: packages=PACKAGES,
      package_data=PACKAGE_DATA,
      data_files=DATA_FILES,
      install_requires=requirements,
      )
