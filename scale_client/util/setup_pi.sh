#!/bin/bash


#Install Dependency
#pip install mosquitto
#pip install pyserial
pip install -r requirements.txt

#Make SCALE start when System boots
cp ../daemons/scale_pi /etc/init.d/scale

update-rc.d scale defaults

#Start SCALE
/etc/init.d/scale start
