#!/bin/bash

#first get the necessary dependencies
apt-get update
apt-get install -y python-m2crypto python-pip python-dev git python-sphinx\
 python-requests python-yaml python-zmq dctrl-tools msgpack-python

#download the saltstack source and build deb files out of it
GIT_SSL_NO_VERIFY=true git clone https://github.com/saltstack/salt.git
cd salt
# force salt to use pure python implementation of msgpack since we are experiencing ARM architecture bugs
sed -i '/^    import msgpack$/a\    raise ImportError' salt/payload.py
sed -i '/^    import msgpack$/a\    raise ImportError' salt/states/pkg.py
debian/rules binary
