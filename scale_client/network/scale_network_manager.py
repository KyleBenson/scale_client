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
        self.scan_all_interfaces()
        self.update_neighbors()
        
    def get_batman_interface(self):
        return self.BATMAN_INTERFACE

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
        '''
        Get ipv4 address of a specific interface
        '''

        if interface in self.interfaces.keys():
            return self.interfaces[interface]['ip']
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

        output = open(self.BATMAN_ORIGINATOR_FILE, 'r')
        
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
        return

    def get_neighbors(self):
        self.update_neighbors()
        return self.neighbors
    
    def scan_neighbors_ip_address(self):
        '''
        Batman advanced operates on layer 2 which does not require ip address.
        We need to have a list neighbors ip address to allow them communicate 
        with each other. This method send 1 ping to every ip addresses that are 
        close the current node ip address
        '''
        batman_ip = self.get_interface_ip_address('wlan0:avahi')
        
        if batman_ip:
            ip_elements = batman_ip.split('.')
            
        if ip_elements:
            if ip_elements[2]:
                #print 'element 2 ' + ip_elements[2]
                slash_16_ip_block = ip_elements[0] + '.' + ip_elements[1]
                slash_24_element = ip_elements[2]
                #print slash_24_element
                self.slash_16_incremental_scanning(slash_16_ip_block, slash_24_element)
        return

    def slash_16_incremental_scanning(self, slash_16_ip_block, slash_24_element):
        '''
        Ideally, we need to scan the whole slash 16 of 169.254.0.0 to find 
        ipv4 associated with mac addresses from batman originators list
        (a list of neighbors mac addresses). However, this is an expensive operation.
        Avahi auto ip assignment seems to pick ip addresses that are close to the current
        active nodes when it allocates new ip address to joining nodes. Therefore, we just
        need to scan neighbor ips in the range of current node (go down and up 5 slash 24)
        '''
        scan_start_point = int(slash_24_element) - 5;
        scan_end_point = int(slash_24_element) + 5;
        if scan_start_point < 1:
            scan_start_point = 1;
    
        # Update neighbbors list before scanning for their ip address
        self.update_neighbors()

        for scanning_slash_24_element in range (scan_start_point, scan_end_point):
            #check to see if all neighbors ip address
            #have been identified
            if self.neighbors_are_all_scanned():
                return
            
            slash_24_ip_block = slash_16_ip_block + '.' + str(scanning_slash_24_element)
            
            self.scan_subnet_slash_24(slash_24_ip_block)
            self.scan_arp_address()

        return 

    def neighbors_are_all_scanned(self):
        '''
        Check to see if all neighbors in the neighbor list
        have been identified their ipv4 address through scanning
        '''
        for index in self.neighbors:
            if not self.neighbors[index].get_ip_address().strip():
                return False
        return True

    def scan_subnet_slash_24(self, slash_24_ip_block):
        host_batman_ip = self.get_interface_ip_address('wlan0:avahi')
        with open(os.devnull, "wb") as limbo:
            for n in range(1, 255):
                ip = slash_24_ip_block + ".{0}".format(n)
                
                if ip != host_batman_ip:
                    subprocess.Popen(["ping", "-c", "1", "-n", "-W", "1", ip], stdout=limbo, stderr=limbo)
        return
                                                                                                                                                                  
    def scan_arp_address(self):
        '''
        Look for neighbors ip address from ARP cache table
        '''
        command = "arp -n | grep {0}".format(self.get_batman_interface())

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

        #mac_ip_table['00:87:35:1c:77:f6'] = '192.168.0.1' 
        #testing ... 

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
            print "Neighbor mac address " + neighbor.get_mac_address()
            print "Neighbor ip address " + str(neighbor.get_ip_address())
            print "Neighbor last seen " + neighbor.get_last_seen()

        return
