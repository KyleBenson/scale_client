#!/bin/bash


echo 0 | sudo tee -a /sys/class/leds/led0/brightness
echo mmc0 | sudo tee -a /sys/class/leds/led0/trigger
