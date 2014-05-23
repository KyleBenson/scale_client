#!/bin/bash

#first get the necessary dependencies
apt-get update
apt-get install -y python-m2crypto python-pip python-dev git python-sphinx\
 python-requests python-yaml python-zmq dctrl-tools msgpack-python

#download the saltstack source and build deb files out of it
GIT_SSL_NO_VERIFY=true git clone https://github.com/saltstack/salt.git
cd salt
debian/rules binary
