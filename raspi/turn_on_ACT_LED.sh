#!/bin/bash

echo none | sudo tee -a /sys/class/leds/led0/trigger
echo 1 | sudo tee -a /sys/class/leds/led0/brightness
