#!/bin/bash

# sets up a newly installed Sheevaplug, including connecting it to the salt-master

MASTER_ADDRESS=SALT_MASTER_IP

# this doesn't work as saltstack.org doesn't have ARMEL support
#wget --no-check-certificate http://bootstrap.saltstack.org -O install_salt.sh
#sudo sh install_salt.sh git develop

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
apt-get install -y python-m2crypto python-pip python-dev git python-sphinx\
 python-requests python-yaml python-zmq dctrl-tools msgpack-python

# install salt from source using dpkg
git clone https://github.com/saltstack/salt.git
cd salt
debian/rules binary
cd ..
dpkg -i salt-common_*.deb salt-minion*.deb
apt-get -f install

# setup minion
echo "master: $MASTER_ADDRESS" > /etc/salt/minion
salt-minion -d

echo "Go to your master and accept the new key from this minion"
