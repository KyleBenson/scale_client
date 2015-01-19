#!/bin/bash

echo "Now we'll migrate everything to the SD card... You did put a two-partition ext-formatted SD card in right?"

# mount partitioned SD card
mkdir /mnt/usr
mkdir /mnt/var
mount /dev/mmcblk0p1 /mnt/usr
mount /dev/mmcblk0p2 /mnt/var
mv /usr/* /mnt/usr/
mv /var/* /mnt/var/

# make sure tmpfs folder exist and are clean
mkdir /mnt/var/lock
mkdir /mnt/var/proc
mkdir /mnt/var/run
rm /mnt/var/lock/*
rm /mnt/var/proc/*
rm /mnt/var/run/*

# clean-up
umount /mnt/usr
umount /mnt/var

# update /etc/fstab
echo "# /etc/fstab: static file system information.
#
# Use 'blkid' to print the universally unique identifier for a
# device; this may be used with UUID= as a more robust way to name devices
# that works even if disks are added and removed. See fstab(5).
#
# <file system> <mount point>   <type>  <options>       <dump>  <pass>
proc            /proc           proc    defaults        0       0
/dev/ubi0_0  /               ubifs   defaults,noatime,rw                    0 0
/dev/mmcblk0p1  /usr         ext2       defaults        0       0
/dev/mmcblk0p2  /var         ext2       defaults        0       0
tmpfs      /var/run        tmpfs   size=1M,rw,nosuid,mode=0755              0 0
tmpfs      /var/lock       tmpfs   size=1M,rw,noexec,nosuid,nodev,mode=1777 0 0
tmpfs      /tmp            tmpfs   defaults,nosuid,nodev                    0 0" > /etc/fstab

reboot

