#!/bin/bash

# sets up a newly installed Sheevaplug, including connecting it to the salt-master

MASTER_ADDRESS=SALT_MASTER_IP # <--- CHANGE THIS !!!!!!

#TODO: this automatically
echo 'Make sure we blew away the old file for original plug eth0!'

# Change the hostname to something new, unique, and identifying
echo "What is the hostname for this device? (Leave blank to keep old one)"
read
OLD_HOSTNAME=`hostname`
if [ "$REPLY" == "" ]; then
    REPLY=$OLD_HOSTNAME
fi
echo "$REPLY" > /etc/hostname
sed "s/$OLD_HOSTNAME/$REPLY/g" -i /etc/hosts
/etc/init.d/hostname.sh start

# install salt dependencies
#TODO: psutil, jinja2
apt-get update
apt-get upgrade
apt-get install -y python-m2crypto python-pip python-dev git python-sphinx\
 python-requests python-yaml python-zmq dctrl-tools msgpack-python
# msgpack-python has an issue on ARM architectures, which we're using, so we need to use a pure Python implementation
pip install msgpack-pure

# install salt using dpkg files that you built with build_salt_debs.sh
dpkg -i salt-common_*.deb
dpkg -i salt-minion*.deb
apt-get -f install

# point minion to the master, run it, and set to run on startup
echo "master: $MASTER_ADDRESS" > /etc/salt/minion
echo "$REPLY" > /etc/salt/minion_id
salt-minion -d

echo "Go to your master and accept the new key from this minion"
