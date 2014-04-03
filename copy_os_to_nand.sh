#!/bin/bash

apt-get install mtd-utils
ubiformat /dev/mtd2 -s 512; ubiattach /dev/ubi_ctrl -m 2; ubimkvol /dev/ubi0 -N rootfs -m;
mkfs.ubifs --compr=zlib /dev/ubi0_0; mount -t ubifs ubi0:rootfs /mnt
mkdir /tmp/rootfs; mount -o bind / /tmp/rootfs/; cp -a /tmp/rootfs/* /mnt/; cp -a /boot /mnt/

# this file holds device-specific information that we want to repopulate on reboot of the new device (ethernet MAC address specifically)
rm /mnt/etc/udev/rules.d/70-persistent-net.rules 

reboot
