#!/usr/bin/python

SALT_MINION_D = "/etc/salt/minion.d"
SALT_CONFIG_FILE = SALT_MINION_D + "/" + "scale.conf"
SALT_ID_PREFIX = "SCALERPi"
SALT_MASTER = ""
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
