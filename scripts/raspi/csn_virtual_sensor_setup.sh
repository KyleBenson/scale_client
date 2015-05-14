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
apt-get install python-protobuf

ln -s ../../CsnBin/csnd /usr/bins/ 
ln -s ../../CsnBin/csn-config /usr/bins/ 

cp csnd /etc/init.d/
update-rc.d csnd defaults
/etc/init.d/csnd start

echo "127.0.0.1 csn-server.appspot.com" >> /etc/hosts 
