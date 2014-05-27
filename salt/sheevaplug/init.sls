# install working drivers for our wi-fi dongles

wifi_driver:
  file.managed:
    - name: /lib/modules/3.2.0-4-kirkwood/kernel/net/wireless/8192cu.ko
    - source: salt://sheevaplug/8192cu.ko
    - user: root
    - group: root
    - mode: 644

blacklist.conf:
  file.append:
    - name: /etc/modprobe.d/blacklist.conf
    - text: blacklist rtl8192cu

/etc/modules:
  file.append:
    - text: 8192cu

install_driver:
  cmd.wait:
    - name: depmod -a
    - watch:
      - file: wifi_driver
      - file: blacklist.conf
      - file: /etc/modules

# now set up the network

wpasupplicant:
  pkg.installed

/etc/network/interfaces:
  file.append:
    - text:
      - allow-hotplug wlan0
      - auto wlan0
      - iface wlan0 inet manual
      - wpa-roam /etc/wpa_supplicant/wpa_supplicant.conf
    - require:
      - cmd: install_driver

wpasupplicant_conf:
  file.managed:
    - name: /etc/wpa_supplicant/wpa_supplicant.conf
    - source: salt://sheevaplug/wpa_supplicant.conf
    #TODO: add box-specific networks? via grains or pillars?
    - require:
      - file: /etc/network/interfaces

# reload networking once we've enabled everything
networking:
  cmd.wait:
    #NOTE: we can't use service.running here because network service has no 'status' argument, so it will always run
    - name: service networking reload
    - watch:
      - file: wpasupplicant_conf
