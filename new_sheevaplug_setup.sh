#!/bin/bash

# sets up a newly installed Sheevaplug, including connecting it to the salt-master

# this doesn't work as saltstack.org doesn't have ARMEL support
#wget --no-check-certificate http://bootstrap.saltstack.org -O install_salt.sh
#sudo sh install_salt.sh git develop

#TODO: set the hostname correctly
echo "don't forget to set the hostname!"

apt-get install python-m2crypto python-pip python-dev 
#python-zeromq?
pip install pyzmq PyYAML pycrypto msgpack-python jinja2 psutil
pip install salt
