# Easy Setup Instruction Step by Step    
## Requirement    
#### Hardware  
* Required  
    * Raspberry Pi 2
    * TF(MicroSD card) card (at least 8GB)
    * TF Card or SD Card Reader
    * Wi-Fi Dongle
    * Ethernet Cable
    * MicroUSB Cable
    * 5V USB Power Supply (2A recommended, at least 1A)

* Optional
    * Analog-Digital-Convertor(ADC) Board (SPI / I2C)
    * Sensors
    * USB-to-TTL Board(e.g.: FT232 or PL2303)
    * HDMI Cable and HDMI Diskplay
    * USB Keyboard & Mouse

#### Software
* Required
    * Tool for Writing Image to SD card. Refer to: [INSTALLING OPERATING SYSTEM IMAGES](https://www.raspberrypi.org/documentation/installation/installing-images/README.md)
    * [SCALE-customized Raspbian image](https://onedrive.live.com/redir?resid=DEE587B7CF2B9C26!1145&authkey=!AD1p3MoE2IOZ2lU&ithint=file%2czip)
    * SSH Client

## Steps
#### Write the SCALE-customized Raspbian Image to SD Card
1. Download [SCALE-customized Raspbian image](https://onedrive.live.com/redir?resid=DEE587B7CF2B9C26!1145&authkey=!AD1p3MoE2IOZ2lU&ithint=file%2czip)
2. Use proper software to write the image to TF card though card reader. Please refer to: [INSTALLING OPERATING SYSTEM IMAGES](https://www.raspberrypi.org/documentation/installation/installing-images/README.md)

#### Connect All Devices and Cables
1. Connect the cables and devices except the power cable. 
2. Connect power cable. 
3. You should be able to see the red LED light is on. The green LED should blink, indicating that the Pi is loading the system from TF card.

#### Login to The System
Credential for The System:
username: __pi__
password: __DSMSCALE__
We recommend using SSH to login to the system.

If Raspberry Pi's IP address is unknown or it is not connected to network yet, there are serveral ways to login to the system.

1. Serial port.
2. HDMI display and USB keyboard and mouse
3. Connected to local router through Ethernet cable. Figure out the IP address by looking up it in router's connected devices list

#### Configure Wireless Setting
The system uses wpa\_supplicant as its wireless network manager. Modify the config file of wpa\_supplicant properly so that the Pi could connect to your wireless network.

Assuming you have a wireless network with SSID "*network_SSID*" and a password "*password*"

1. Run command `ifconfig` to make sure wlan device is in the network interface list.
2. Generate the secure key using the following command if your wireless network has a password:
```
wpa_passphrase network_SSID password
```

3. Copy all the output of previous command (*network={.....}*), and add them to the tail of the wpa\_supplicant config file:
```
sudo vim /etc/wpa_supplicant/wpa_supplicant.conf
```
4. Reboot the system and see if Pi get the wireless connection.

#### Configure SCALE Client
The config file of SCALE clinet is located in _/etc/scale/client/config.yml_. Modify or Overwrite it to fit for your application. If there is no actual sensors and you just want to have a dummy SCALE client. Please run the following commands to use a dummy config file:

```
cd ~
sudo cp -f SmartAmericaSensors/scale_client/config/dummy_config.yml /etc/scale/client/config.yml
```

Restart the SCALE clinet program:
```
sudo service scale_daemon restart
```


#### Verify that SCALE Client Is Working 
1. Visit http://akerue.me/dashboard/dashboard.html
2. Check if your device is sending the data. The Device ID is the last two section of the Wi-Fi dongle MAC address


