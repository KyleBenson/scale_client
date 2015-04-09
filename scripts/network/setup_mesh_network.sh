#!/bin/bash

# This script intall batman, avahi, apring 
# and config mesh network for a node

echo "\nInstalling arping packet...\n"
apt-get update
apt-get install arping
echo "\narping is installed.\n"

echo "\n\nInstalled Batman...\n"
apt-get install batctl
echo "\n\nBatman is installed.\n"

echo "\n\nSetup to load Batman on reboot\n"
modprobe batman-adv
echo "batman-adv" >> /etc/modules

echo "\n\nInstall Avahi auto ip assignment...\n"
apt-get install avahi-daemon avahi-autoipd

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

echo "# setup mesh interface on reboot

ifconfig wlan0 down
ifconfig wlan0 mtu 1532
iwconfig wlan0 mode ad-hoc essid scale-net channel 1
batctl if add wlan0
ifconfig wlan0 up
ifconfig bat0 up
avahi-autoipd wlan0 -D

exit 0" >> /etc/rc.local

echo "\n\nMesh network has been setup succesfully for this node\n\n"
echo "To test, try: batctl 0\n\n"
echo "You will see a list of neighbors' mac address if the node is with coverage range of other nodes"
