import logging
logging.basicConfig()
log = logging.getLogger(__name__)

import subprocess
import shlex
from pprint import pprint

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
    neighbors = {}	
    BATMAN_INTERFACE = 'wlan0'
    BATMAN_ORIGINATOR_FILE = '/sys/kernel/debug/batman_adv/bat0/originators'

    def __init__(self):
        self.interfaces['eth0'] = {'ip': '', 'mac': '', 'status': 'down'}
        self.interfaces['bat0'] = {'ip': '', 'mac': '', 'status': 'down'}
        self.interfaces['wlan1'] = {'ip': '', 'mac': '', 'status': 'down'}
        self.interfaces['wlan0'] = {'ip': '', 'mac': '', 'status': 'down'}
        self.interfaces['wlan0:avahi'] = {'ip': '', 'mac': '', 'status': 'down'}
        self.scan_all_interfaces();
        
    def get_batman_interface(self):
        return self.BATMAN_INTERFACE

    def scan_all_interfaces(self):
        #Scan to get ipv4 and mac address of all 
        #available interfaces on the device
        # scan for ipv4 addresses
        for interface in self.interfaces:
            command = "ifconfig {0} | grep 'inet addr'".format(interface)
            proc = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
            output, error = proc.communicate()
            exitcode = proc.returncode
            if len(error) == 0:
                found = re.search("addr:(.+?) ", output)
                if found:
                    self.interfaces[interface]['ip'] = found.group(1)
                    self.interfaces[interface]['status'] = 'up'

        #scan for mac addresses
        for interface in self.interfaces:
            command = "ifconfig {0} | grep 'HWaddr'".format(interface)
            proc = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
            output, error = proc.communicate()
            exitcode = proc.returncode
            
            if len(error) == 0:
                found = re.search("HWaddr(.+?) ", output)
                if found:
                    self.interfaces[interface]['mac'] = found.group(1)
        return
    
    def get_interface_ip_address(self, interface):
        if interface in self.interfaces.keys():
            return self.interfaces[interface]['ip']
        else:
			         return 

    def get_interface_status(self, interface):
        if interface in self.interfaces.keys():
            return self.interfaces[interface]['status']
        else:
			         return 

    def get_neighbors_mac_address(self):
        output = open(self.BATMAN_ORIGINATOR_FILE, 'r')
        
        line_index = 0
        for line in output:
            if line_index > 1:
                if len(line) > 0:
                    parts = line.split(' ')
                    if len(parts[0]) > 0:
                        print parts
                        neighbor = Neighbor(parts[0], 0, parts[4])
                        print neighbor
                        self.neighbors[parts[0]] = neighbor
                        
            line_index += 1
        return

    def get_neighbors(self):
        self.get_neighbors_mac_address()
        return self.neighbors
    
    def scan_neighbors_ip_address(self):
        batman_ip = self.get_interface_ip_address('wlan0:avahi')
        
        print batman_ip
        
        if batman_ip:
            ip_elements = batman_ip.split('.')
            print ip_elements
            
        if ip_elements:
            if ip_elements[2]:
                print 'element 2 ' + ip_elements[2]
                slash_16_ip_block = ip_elements[0] + '.' + ip_elements[1]
                slash_24_element = ip_elements[2]
                print slash_24_element
                #self.slash_16_incremental_scanning(slash_16_ip_block, slash_24_element)
        return

    def slash_16_recursive_scanning(self, slash_16_ip_block, slash_24_element):
        if (slash_24_element > 254 or slash_24_element) < 1:
            return 0
        else:
            slash_24_ip_block = slash_16_ip_block + '.' + slash_24_element
            self.scan_subnet_slash_24(slash_24_ip_block)
            self.scan_arp_address()

            self.slash_16_recursive_scanning(slash_16_ip_block, slash_24_element + 1)
            self.slash_16_recursive_scanning(slash_16_ip_block, slash_24_element - 1)
            
            
    def scan_subnet_slash_24(self, slash_24_ip_block):
        with open(os.devnull, "wb") as limbo:
            for n in xrange(1, 254):
                ip = ip_block + "{1}".format(n)
                subprocess.Popen(["ping", "-c", "1", "-n", "-W", "1", ip], stdout=limbo, stderr=limbo)
                print(ip)
                
        return
                                                                                                                                                                  
    def scan_arp_address(self):
        current_neighbors = self.get_neighbors_mac_address()

        print current_neighbors

        command = "arp -n | grep {0}".format(self.get_batman_interface())

        proc = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
        output, error = proc.communicate()
        exitcode = proc.returncode
        
        if not error:
            print output
        else:
            print 'somthing is going wrong'
        return

    def display_neighbors(self):
        self.get_neighbors_mac_address()
        for neighbor in self.neighbors:
            print neighbor
            
        for index, item in enumerate(self.neighbors):
            print(index, item)

        return
