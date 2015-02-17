'''
Class to handle network operation 
for SCALE client node, writen by

Andy Nguyen <phuhn@uci.edu>

'''
import subprocess
import shlex
from subprocess import Popen, PIPE

import re
import os

class Neighbor():
	mac_address = ''
	ip_address = ''
	last_seen = ''

	def __init__(self, mac_addr, ip_addr, last_seen):
		self.mac_address = mac_addr
		self.ip_address = ip_addr
		self.last_seen = last_seen

	def get_mac_address(self):
		return self.mac_address

	def get_ip_address(self):
		return self.ip_address

	def get_last_seen(self):
		return self.last_seen

	def set_mac_address(self, mac_addr):
		self.mac_address = mac_addr

	def set_ip_address(self, ip_addr):
		self.ip_address = ip_addr

	def set_last_seen(self, last_seen):
		self.last_seen = last_seen




class ScaleNetworkManager():
	interfaces = {}	
	neighbors= {}

	batman_interface = ''
	batman_originors_file = ''

	def __init__(self):
		self.interfaces['eth0'] = 0
		self.interfaces['wlan0:avahi'] = 0
		self.interfaces['wlan0'] = 0
		self.interfaces['wlan1'] = 0
		self.interfaces['bat0'] = 0

		self.batman_interface = 'wlan0'		
		self.batman_originors_file = '/sys/kernel/debug/batman_adv/bat0/originators'
		return

	def scan_all_interfaces(self):
		for interface in self.interfaces:
			command = "ifconfig {0} | grep 'inet addr'".format(interface)
			proc = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
			output, error = proc.communicate()
			exitcode = proc.returncode
			
			if len(error) == 0:	
				found = re.search("addr:(.+?) ", output)
				if found:
					self.interfaces[interface] = found.group(1)
		return

	def get_interface_status(self, interface):
		if interface in self.interfaces.keys():
			return self.interfaces[interface]
		else:
			return 0
		return

	def get_neighbors_mac_address(self):
		output = open(self.batman_originors_file, 'r')
		
		line_index = 0		
		for line in output:
			if line_index > 1:
				if len(line) > 0:
					parts = line.split(' ')
					if len(parts[0]) > 0:
						neighbor = Neighbor(parts[0], 0, parts[4]);
						self.neighbors[parts[0]] = neighbor
		
			line_index += 1
		return

	def get_neighbors(self):
		return self.neighbors		

	def scan_neighbors_ip_address(self):
		return 1
	
