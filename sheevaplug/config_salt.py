#!/usr/bin/python

# NOTICE
# 1) Make sure Raspberry Pi is loaded with the latest image, which has a salt installation.
# 2) You should be able to write to the configuration directory.
# 3) Fill in the IP address and port of salt master before running this script.

SALT_MINION_D = "/etc/salt/minion.d"
SALT_CONFIG_FILE = SALT_MINION_D + "/" + "scale.conf"
SALT_ID_PREFIX = "sheevaplug"
SALT_MASTER = "128.195.11.110" #"208.76.112.106"
SALT_MASTER_PORT = 4506

from uuid import getnode

conf = """id: %s%s
master: %s
master_port: %d
""" % (SALT_ID_PREFIX, ("%012x" % getnode())[6:], SALT_MASTER, SALT_MASTER_PORT)

print conf

f = open(SALT_CONFIG_FILE, "w")
f.write(conf)
f.close()
