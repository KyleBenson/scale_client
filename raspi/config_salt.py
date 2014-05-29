#!/usr/bin/python

# NOTICE
# 1) Make sure Raspberry Pi is loaded with the latest image,
#    which has a salt installation.
# 2) You should be able to write to the configuration directory.
# 3) Fill in the IP address and port of salt master before running this script.

import subprocess

# remove charles's user info
subprocess.call('userdel charles; rm -rf /home/charles; rm -rf /home/SmartAmericaSensors', shell=True)

SALT_CONFIG_FILE = "/etc/salt/minion"
SALT_MASTER = "192.168.1.102 #208.76.112.106"
SALT_MASTER_PORT = 4506
SALT_ID_PREFIX = "raspi"

# set hostname using last characters of MAC address as unique ID
from uuid import getnode

SALT_ID_SUFFIX = ("%012x" % getnode())[6:]
SALT_HOSTNAME = SALT_ID_PREFIX + SALT_ID_SUFFIX

with open('/etc/hostname') as f:
    old_hostname = f.read().strip()
with open('/etc/hostname', 'w') as f:
    f.write(SALT_HOSTNAME)

# update hosts file
with open('/etc/hosts') as f:
    old_hosts = f.read().strip()
with open('/etc/hosts', 'w') as f:
    f.write(old_hosts.replace(old_hostname, SALT_HOSTNAME))

# must restart this service to register hostname change
subprocess.call('/etc/init.d/hostname.sh start', shell=True)

conf = """id: %s
master: %s
master_port: %d
""" % (SALT_HOSTNAME, SALT_MASTER, SALT_MASTER_PORT)

print conf

f = open(SALT_CONFIG_FILE, "w")
f.write(conf)
f.close()

subprocess.call('rm -rf /etc/salt/minion.d/; rm /etc/salt/pki/minion/minion_master.pub; service salt-minion restart', shell=True)
print "Go to your master and accept the new key from this minion"
