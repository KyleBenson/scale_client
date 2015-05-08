import logging
logging.basicConfig()
log = logging.getLogger(__name__)

import subprocess
import json
import shlex
from pprint import pprint

from subprocess import Popen, PIPE

import re
import os
import os.path

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

    def __init__(self, broker, batman_interface="wlan0:avahi", 
                batman_originators_file="/sys/kernel/debug/batman_adv/bat0/originators"):

        self.interfaces['eth0'] = {'ip': '', 'mac': '', 'status': 'down'}
        self.interfaces['bat0'] = {'ip': '', 'mac': '', 'status': 'down'}
        self.interfaces['wlan1'] = {'ip': '', 'mac': '', 'status': 'down'}
        self.interfaces['wlan0'] = {'ip': '', 'mac': '', 'status': 'down'}
        self.interfaces['wlan0:avahi'] = {'ip': '', 'mac': '', 'status': 'down'}
        self.batman_interface = batman_interface
        self.batman_originators_file = batman_originators_file
        self.scan_all_interfaces()

        if self.batman_is_active():
            self.update_neighbors()
            
        self.broadcast_host_ip()
        self.scan_arp_address();
        
    def batman_is_active(self):
        if os.path.isfile(self.batman_originators_file):
            return True
        else:
            return False

    def get_batman_interface(self):
        return self.batman_interface

    def scan_all_interfaces(self):
        '''
        Scan to get ipv4 and mac address of all 
        available interfaces on the device
        '''
        
        #scan for ipv4 addresses
        for interface in self.interfaces:
            command = "ifconfig {0} | grep 'inet addr'".format(interface)
            proc = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
            output, error = proc.communicate()
            exitcode = proc.returncode
            if len(error) == 0:
                found = re.search("addr:(.+?) ", output)
                if found:
                    self.interfaces[interface]['ip'] = found.group(1).strip()
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
                    self.interfaces[interface]['mac'] = found.group(1).strip()
        return
    

    def broadcast_host_ip(self):
        '''
        Batman only provides neighbors's mac address,
        which can not be used to send/receive data at 
        application level (layer 7). Nodes need to know
        their neighbors' ip addresses to communicate with 
        each other in local mesh network. To do that, they
        have to broadcast their assigned ip address when 
        they join the network. Arping packet allows them 
        to do so. This method works based on assumption that
        Arping has been installed on the node
        (sudo apt-get install arping)
        '''
        batman_ip_address = self.get_interface_ip_address(self.batman_interface)
        if batman_ip_address:
            # annouce node's ip address to other neighbor nodes
            command = "arping -A " + batman_ip_address + " -c 1"
            log.info("Broadcast node ip: " + command)

            proc = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
            output, error = proc.communicate()
            exitcode = proc.returncode
            
            if error:
                error_msg = "Failed to broadcast node ip, arp packet may not be installed."
                error_msg += "Error: " + json.dumps(error)
                log.error(error_msg);

                return False
            else:
                return True

    def get_interface_ip_address(self, interface):
        '''
        Get ipv4 address of a specific interface
        '''

        if interface in self.interfaces.keys():
            return self.interfaces[interface]['ip']
        else:
			         return  

    def get_interface_mac_address(self, interface):
        '''
        Get mac address of a specific interface
        '''

        if interface in self.interfaces.keys():
            return self.interfaces[interface]['mac']
        else:
			         return  

    def get_interface_status(self, interface):
        '''
        Check status of a specific interface
        up is active, down is inactive
        '''

        if interface in self.interfaces.keys():
            return self.interfaces[interface]['status']
        else:
			         return 

    def update_neighbors(self):
        '''
        Get a list of neighbors' mac address form batman advanced
        and construct a neighbors list which contains ipv4, mac address
        and last seen
        '''

        try:
            output = open(self.batman_originators_file, 'r')
        
            line_index = 0
            for line in output:
                if line_index > 1:
                    if len(line) > 0:
                        parts = line.split(' ')
                        if len(parts[0]) > 0:
                            mac_address = parts[0].strip()
                            if mac_address not in self.neighbors.keys():
                                neighbor = Neighbor(mac_address, '', parts[4])
                                self.neighbors[mac_address] = neighbor
                            else:
                                self.neighbors[mac_address].set_last_seen(parts[4])

                line_index += 1
        except AttributeError:
            log.error('Failed to open batman orginators file')

        return

    def get_neighbors(self):
        # Get new neighbors from
        # batman originators list
        self.update_neighbors()

        # Get up-to-date neighbors
        ## ip address from arp table
        self.scan_arp_address();
        return self.neighbors
    
                                                                                                                                                                  
    def scan_arp_address(self):
        '''
        Look for neighbors ip address from ARP cache table
        '''

        batman_physical_interface = self.batman_interface.replace(":avahi", "")
        command = "arp -n | grep {0}".format(batman_physical_interface)

        proc = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
        output, error = proc.communicate()
        exitcode = proc.returncode
        
        if not error:
            mac_ip_table = self.get_mac_ip_table(output)

            if self.neighbors:
                for index in self.neighbors:
                    if index in mac_ip_table.keys():
                        self.neighbors[index].set_ip_address(mac_ip_table[index])
        else:
            log.debug("Scanning neighbors ip, failed to run the command " + command)

        return

    def get_mac_ip_table(self, result_string):
        '''
        Construct a dictionary that map mac address to its host ipv4 
        address basing on the result for apr -n command 
        '''
        mac_ip_table = {}

        lines = result_string.split('\n')

        for line in lines:
            #check to see if the arp line result contains a mac address
            try:
                found = re.search(r'([0-9A-F]{2}[:-]){5}([0-9A-F]{2})', line, re.I)
            except AttributeError:
                found = ''
        
            if found:
                mac_address = found.group(0).strip()
                log.debug("Scanning neighbor ip, found a mac address " + mac_address)
                
                # get ipv4 address from the scan arp result line
                try:
                    found = re.search(r'((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9])', line, re.I)
                except AttributeError:
                    found = ''

                if found:
                    ipv4_address = found.group(0).strip()
                    log.debug("Scanning neighbors ip, found an IPV4: " + ipv4_address)
                    mac_ip_table[mac_address] = ipv4_address
                else:
                    log.debug("Scanning neighbors ip, error: can not find ipv4 in arp line result")

        return mac_ip_table


    def display_neighbors(self):
        for index in self.neighbors:
            neighbor = self.neighbors[index]
            print "Neighbor mac address: " + neighbor.get_mac_address()
            print "Neighbor ip address: " + str(neighbor.get_ip_address())
            print "Neighbor last seen: " + neighbor.get_last_seen()

        return
