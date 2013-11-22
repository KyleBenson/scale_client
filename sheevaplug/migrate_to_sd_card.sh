#!/bin/bash

echo "Now we'll migrate everything to the SD card... You did put an SD card in right?"

mkdir /mnt/usr
mkdir /mnt/var
mount /dev/mmcblk0p1 /mnt/usr
mount /dev/mmcblk0p2 /mnt/var
mv /usr/* /mnt/usr/
mv /var/* /mnt/var/
rm /mnt/var/lock/*
rm /mnt/var/proc/*
rm /mnt/var/run/*
