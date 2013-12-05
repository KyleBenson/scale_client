#!/bin/bash


#Install Dependency
pip install mosquitto
pip install pyserial

#Make SCALE start when System boots
cp scale_pi /etc/init.d/scale

update-rc.d scale defaults

#Start SCALE
/etc/init.d/scale start
