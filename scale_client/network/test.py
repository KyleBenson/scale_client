from scale_network_manager import ScaleNetworkManager

network_manager = ScaleNetworkManager()

network_manager.scan_all_interfaces()

eth0_ip = network_manager.get_interface_status('eth0')
wlan1_ip = network_manager.get_interface_status('wlan1')
bat0_ip = network_manager.get_interface_status('wlan0:avahi')

print eth0_ip	
print wlan1_ip	
print bat0_ip	

network_manager.get_neighbors_mac_address()

network_manager.get_neighbors()
