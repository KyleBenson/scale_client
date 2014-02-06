#!/bin/sh

archive=csn.tar.gz
password=$1

echo "Installing software."

pip install WebOb
pip install Paste
pip install webapp2
apt-get install python-protobuf

wget http://ftp.us.debian.org/debian/pool/main/o/openssl/libssl0.9.8_0.9.8o-4squeeze14_armel.deb
dpkg -i libssl0.9.8_0.9.8o-4squeeze14_armel.deb

cd /
wget http://csn.cacr.caltech.edu/code/latest/linux/plug/$archive
tar mxzf $archive
rm $archive
update-rc.d csnd defaults
/etc/init.d/csnd start
cd

echo "Installing SSH key."
mkdir .ssh
chmod go-rx .ssh
cat <<EOF > .ssh/authorized_keys
ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA8hsPB4L3hSuqUzzi0Ewa6+UDk/6ibRrUm820YVvmzZ3FGGlno80EUfUo3GlNubfLhme2h5tn4e7+sqriH4jtc46+Y0dzVdu5cHcwMMSGxbkj8FXg6sochXA+es8c2B49JOivQ0Sv8VxwdEFeddGLCrci4bkOd+QMCdXcWjbBah1O1zhSQMWT//skNLsB21RYCpBRAi3l/3iXjqDw4KDhbTNd/CV4N7u+Ch/CbzFfFZDJzyXwyCC79f2rk4x5k9bEO3wgCRlqKBIp0g0lIZ1Yb2FTvJziacbBHNSFLJO8z99HEtqNo7kV1/CS6VhyyMQLw8vyX++A/AmRnDhTrcj+6w== leif@crust
EOF

echo "Setting root password."
echo $password > tmp
echo $password >> tmp
passwd < tmp
rm tmp

echo "Waiting for registration."
status=1
while [ $status -ne 0 ]
do
sleep 2
    grep id /etc/CSNClientSettings
    status=$?
done
id=`grep id /etc/CSNClientSettings | awk '{ print $2 }'`
hwAddr=`ifconfig | grep HWaddr | awk '{print $5}'`

echo "Inserting EmbeddedSystem record."
wget -q -O - "http://csn.cacr.caltech.edu/clients/embedded.html?hwAddr=$hwAddr&kind=SheevaPlug&client=$id&password=$password"
echo

echo "Done."
echo
echo "url: http://csn.cacr.caltech.edu/clients/$id/"

csn-config set-location 34.13834 -118.12443 1
rm libssl0.9.8_0.9.8o-4squeeze14_armel.deb
# shutdown -h now


