#!/bin/bash

# This script intall batman, avahi, apring 
# and config mesh network for a node

echo ""
echo "Installing arping packet..."
echo ""

apt-get update
apt-get install -y arping
echo ""
echo "arping is installed."
echo ""

echo ""
echo ""
echo "Installed Batman..."
echo ""

apt-get install -y batctl
echo ""
echo ""
echo "Batman is installed."
echo ""

echo ""
echo ""
echo "Setup to load Batman on reboot"
echo ""

modprobe batman-adv
echo "batman-adv" >> /etc/modules

echo ""
echo ""
echo "Install Avahi auto ip assignment..."
echo ""
apt-get install -y avahi-daemon avahi-autoipd

echo "Config Mesh Interface ..."

echo "auto lo
iface lo inet loopback
iface eth0 inet dhcp

allow-hotplug wlan1
iface wlan1 inet manual
wpa-roam /etc/wpa_supplicant/wpa_supplicant.conf
iface default inet dhcp

allow-hotplug wlan0
auto wlan0" > /etc/network/interfaces

sed '/exit/d' /etc/rc.local > /etc/rc.local

echo "# setup mesh interface on reboot

ifconfig wlan0 down
ifconfig wlan0 mtu 1532
iwconfig wlan0 mode ad-hoc essid scale-net channel 1
batctl if add wlan0
ifconfig wlan0 up
ifconfig bat0 up
avahi-autoipd wlan0 -D

exit 0" >> /etc/rc.local

/etc/rc.local

echo ""
echo ""
echo "Running test"
echo ""
echo ""
batctl o

echo ""
echo ""
echo "Mesh network has been setup succesfully for this node"
echo ""
echo ""
echo "To test, try: batctl 0"
echo ""
echo "You will see a list of neighbors' mac address if the node is with coverage range of other nodes"
echo ""
echo "You can also do ifconfig to verify if batman has been setup correctly. wlan0:avahi with an ipv4"
echo "in ifconfig result indicates the setup is succesfully"
 
