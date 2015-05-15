#!/bin/sh

echo "Installing software."

unlink /etc/CsnClientSettings
unlink /etc/CsnClientPublickey

sudo apt-get update -y
sudo apt-get install curl -y
sudo apt-get install libssl-dev -y

pip install WebOb
pip install Paste
pip install webapp2
apt-get install python-protobuf -y

cp ../../csn_bin/csnd /usr/sbin/ 
cp ../../csn_bin/csn-config /usr/sbin/ 

cp csnd /etc/init.d/
update-rc.d csnd defaults
/etc/init.d/csnd start
