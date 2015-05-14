#!/bin/sh

echo "Installing software."

unlink /etc/CsnClientSettings
unlink /etc/CsnClientPublickey

sudo apt-get update -y
sudo apt-get install curl -y
sudo apt-get install libssl-dev -y
sudo mkdir ../../../deps
sudo ln -s /usr/local/bin ../../../deps
sudo ln -s /usr/local/include ../../ ../deps
sudo ln -s /usr/local/lib ../../../deps
sudo mkdir ../../../library
cd ../../../library

sudo curl -O http://curl.haxx.se/download/curl-7.31.0.tar.bz2
sudo curl -O http://protobuf.googlecode.com/files/protobuf-2.5.0.tar.gz
sudo curl -O http://iweb.dl.sourceforge.net/project/libusb/libusb-1.0/libusb-1.0.9/libusb-1.0.9.tar.bz2

sudo tar xvfj curl-7.31.0.tar.bz2
cd  curl-7.31.0
sudo ./configure
sudo make
sudo make install
cd ../


sudo tar -zxvf protobuf-2.5.0.tar.gz
cd protobuf-2.5.0
sudo ./configure --prefix=/usr/local
sudo make
sudo make install
cd ../


sudo tar xvfj libusb-1.0.9.tar.bz2
cd libusb-1.0.9
sudo ./configure
sudo make
sudo make install
cd ../


pip install WebOb
pip install Paste
pip install webapp2
apt-get install python-protobuf


update-rc.d csnd defaults
/etc/init.d/csnd start

echo "127.0.0.1 csn-server.appspot.com" >> /etc/hosts 
