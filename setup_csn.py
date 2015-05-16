#!/usr/bin/env python

import os, errno
import subprocess

#CSN setup script
CSN_SETUP_SCRIPT = os.getcwd() + "/scripts/raspi/csn_virtual_sensor_setup.sh"
CSND_BIN   = os.getcwd() + "/csn_bin/csnd"
CSN_CONFIG_BIN   = os.getcwd() + "/csn_bin/csn-config"
CSND_INI   = os.getcwd() + "/scripts/raspi/csnd"

# Setup virtual CSNserver and CSN client
try:
    print "Setting up CSN environment ... "
    subprocess.call("sudo apt-get update -y", shell=True)
    subprocess.call("sudo apt-get install curl -y", shell=True)
    subprocess.call("sudo apt-get install libssl-dev -y", shell=True)

    subprocess.call("pip install WebOb", shell=True)
    subprocess.call("pip install Paste", shell=True)
    subprocess.call("pip install webapp2", shell=True)
    subprocess.call("apt-get install python-protobuf -y", shell=True)

    os.system("cp " + CSND_BIN + " /usr/local/sbin/")
    os.system("cp " + CSN_CONFIG_BIN + " /usr/local/sbin/")
    os.system("cp " + CSND_INI + " /etc/init.d/")

    subprocess.call("update-rc.d csnd defaults 98 02", shell=True)
    subprocess.call("/etc/init.d/csnd start", shell=True)
except IOError:
    print "Failed to setup virtual CSN server and CSN client"
