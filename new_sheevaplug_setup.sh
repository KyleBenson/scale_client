#!/bin/bash

# sets up a newly installed Sheevaplug, including connecting it to the salt-master

# this doesn't work as saltstack.org doesn't have ARMEL support
#wget --no-check-certificate http://bootstrap.saltstack.org -O install_salt.sh
#sudo sh install_salt.sh git develop

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

apt-get install -y python-m2crypto python-pip python-dev 
#python-zeromq?
pip install pyzmq PyYAML pycrypto msgpack-python jinja2 psutil
pip install salt
