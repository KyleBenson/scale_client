#!/usr/bin/env python

import os, errno
from setuptools import setup, find_packages

# Generic info about package
NAME = "scale_client"
VERSION = "0.2"
DESC = "Safe Community Awareness and Alerting Network (SCALE) client"
AUTHOR = "Kyle Benson"
AUTHOR_EMAIL = "kebenson@uci.edu"
URL = "https://github.com/KyleBenson/scale_client"

# Specific information about package contents
# PACKAGES = ["scale_client", "scale_client.core",
#             "scale_client.sensors", "scale_client.event_sinks",
#             "scale_client.applications"]
PACKAGE_DATA = {"scale_client": ["config/*"],
                "scale_client.event_sinks": ["sigfox_event_types.json"]}
DAEMON_LOCATION = "/etc/init.d"
CONFIG_LOCATION = "/etc/scale/client"
data_files = []

# Gather requires info from requirements.txt
with open('requirements.txt') as F:
    requirements = [l.strip() for l in F.readlines() if not l.startswith("#")]

# Make config location
# http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

try:
    mkdir_p(CONFIG_LOCATION)
except OSError:
    pass
try:
	with open(CONFIG_LOCATION + "/example_config.yml", "a") as F:
		pass
	data_files.append((CONFIG_LOCATION, ["scale_client/config/example_config.yml"]))
except IOError:
	print "Can't access config location. Skipping config example installation..."

# Check whether we will be able to install the daemon or not
try:
    with open(DAEMON_LOCATION + "/scale_daemon", 'a') as F:
        pass
    data_files.append((DAEMON_LOCATION, ["scripts/scale_daemon"]))
except IOError:
    print "Can't access daemon location. Skipping daemon installation..."

setup(name=NAME,
      version=VERSION,
      description=DESC,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=URL,
      # packages=PACKAGES,
      packages=find_packages(),
      package_data=PACKAGE_DATA,
      data_files=data_files,
      install_requires=requirements,
      )
