#!/bin/sh

archive=csn.tar.gz

echo "Installing software."

pip install WebOb
pip install Paste
pip install webapp2
apt-get install python-protobuf

wget http://ftp.us.debian.org/debian/pool/main/o/openssl/libssl0.9.8_0.9.8o-4squeeze14_armel.deb
dpkg -i libssl0.9.8_0.9.8o-4squeeze14_armel.deb
rm libssl0.9.8_0.9.8o-4squeeze14_armel.deb

cd /
wget http://csn.cacr.caltech.edu/code/latest/linux/plug/$archive
tar mxzf $archive
rm $archive
update-rc.d csnd defaults
/etc/init.d/csnd start
cd

echo "127.0.0.1 csn-server.appspot.com" >> /etc/hosts 
csn-config set-location 34.13834 -118.12443 1
