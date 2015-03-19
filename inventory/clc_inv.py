#!/usr/bin/env python

import sys
import os
import argparse
import re
from time import time
import ConfigParser
import clc

try:
    import json
except ImportError:
    import simplejson as json
    
class clcInventory(object):
    def __init__(self):
        ''' Main execution path '''

        # Inventory grouped by instance IDs, tags, security groups, regions,
        # and availability zones
        self.inventory = {}
        
        # Index of hostname (address) to instance ID
        self.index = {}

        # Read settings and parse CLI arguments
        self.read_settings()
        self.parse_cli_args()

        # Cache
        if self.args.refresh_cache:
            self.do_api_calls_update_cache()
        elif not self.is_cache_valid():
            self.do_api_calls_update_cache()

        # Data to print
        if self.args.host:
            data_to_print = self.get_host_info()

        elif self.args.list:
            # Display list of instances for inventory
            if len(self.inventory) == 0:
                data_to_print = self.get_inventory_from_cache()
            else:
                data_to_print = self.json_format_dict(self.inventory, True)
                
        print data_to_print

    def is_cache_valid(self):
        ''' Determines if the cache files have expired, or if it is still valid '''

        if os.path.isfile(self.cache_path_cache):
            mod_time = os.path.getmtime(self.cache_path_cache)
            current_time = time()
            if (mod_time + self.cache_max_age) > current_time:
                if os.path.isfile(self.cache_path_index):
                    return True

        return False
        
    def read_settings(self):
        ''' Reads the settings from the clc.ini file '''

        config = ConfigParser.SafeConfigParser()
        clc_default_ini_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'clc_settings.ini')
        clc_ini_path = os.environ.get('CLC_INI_PATH', clc_default_ini_path)
        config.read(clc_ini_path)

        if not config.has_section('api'):
            raise ValueError('clc.ini file must contain a [api] section')

        if config.has_option('api', 'v1_api_key'):
            self.v1_api_key = config.get('api','v1_api_key')
        else:
            raise ValueError('clc.ini does not have a v1_api_key defined')

        if config.has_option('api', 'v1_api_passwd'):
            self.v1_api_passwd = config.get('api','v1_api_passwd')
        else:
            raise ValueError('clc.ini does not have a v1_api_passwd defined')

        if config.has_option('api', 'v2_api_username'):
            self.v2_api_username = config.get('api','v2_api_username')
        else:
            raise ValueError('clc.ini does not have a v2_api_username defined')

        if config.has_option('api', 'v2_api_passwd'):
            self.v2_api_passwd = config.get('api','v2_api_passwd')
        else:
            raise ValueError('clc.ini does not have a v2_api_passwd defined')

        clc.v1.SetCredentials(self.v1_api_key,self.v1_api_passwd)
        clc.v2.SetCredentials(self.v2_api_username,self.v2_api_passwd)


        # Cache related
        cache_path = config.get('cache', 'cache_path')
        self.cache_path_cache = cache_path + "/ansible-clc.cache"
        self.cache_path_index = cache_path + "/ansible-clc.index"
        self.cache_max_age = config.getint('cache', 'cache_max_age')


    def _clc_set_credentials(self, config):
        c = config
        e = os.environ

        self.v2_api_username = e['CLC_V2_API_USERNAME']
        self.v2_api_passwd = e['CLC_V2_API_PASSWD']

        clc.v2.SetCredentials(self.v2_api_username, self.v2_api_passwd)

        return clc

    def parse_cli_args(self):
        '''
        Command line argument processing
        '''

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based from CenturyLink Cloud servers and groups')
        parser.add_argument('--list', action='store_true', default=True,
                           help='List instances (default: True)')
        parser.add_argument('--host', action='store',
                           help='Get all the variables about a specific instance')
        parser.add_argument('--refresh-cache', action='store_true', default=False,
                           help='Force refresh of cache by making API requests to CenturyLink Cloud')
        self.args = parser.parse_args()
        
    def do_api_calls_update_cache(self):
        ''' 
        Do API calls to a location, and save data in cache files 
        '''

        self.get_nodes()

    def get_nodes(self):
        '''
        Gets the list of all nodes
        '''

        for node in clc.v1.Server.GetServers(location='VA1',group=None,alias=None):
            self.add_node(node)
            
        self.write_to_cache(self.inventory, self.cache_path_cache)
        self.write_to_cache(self.index, self.cache_path_index)
 
    def get_node(self, node_id):
        '''
        Gets details about a specific node
        '''

        return [node for node in clc.v1.Server.GetServers(location='VA1',group=None,alias=None) if node.ID == node_id][0]


    def add_node(self, node):
        '''
        Adds a node to the inventory and index, as long as it is
        addressable 
        '''

        # Only want running instances
        if node['PowerState'] != "Started":
            return

        # Select the best destination address
        if not node['IPAddress'] == []:
            dest = node['IPAddress']
        if not dest:
            # Skip instances we cannot address (e.g. private VPC subnet)
            return

        # Add to index
        self.index[dest] = node['Name']

        # Inventory: Group by instance ID (always a group of 1)
        self.inventory[node['Name']] = [dest]
        '''
        # Inventory: Group by region
        self.push(self.inventory, region, dest)

        # Inventory: Group by availability zone
        self.push(self.inventory, node.placement, dest)

        # Inventory: Group by instance type
        self.push(self.inventory, self.to_safe('type_' + node.instance_type), dest)
        '''
        # Inventory: Group by key pair
 #       if node.extra['HardwareGroupID']:
 #           self.push(self.inventory, self.to_safe('key_' + node.extra['keyname']), dest)
            
        # Inventory: Group by security group, quick thing to handle single sg
        if node['HardwareGroupUUID']:
            self.push(self.inventory, self.to_safe(self.group_name_from_UUID(node['HardwareGroupUUID'])), dest)

    def group_name_from_UUID(self, uuid):
        return str(clc.v2.Group(id=uuid))
        
    def get_host_info(self):
        '''
        Get variables about a specific host
        '''

        if len(self.index) == 0:
            # Need to load index from cache
            self.load_index_from_cache()

        if not self.args.host in self.index:
            # try updating the cache
            self.do_api_calls_update_cache()
            if not self.args.host in self.index:
                # host migh not exist anymore
                return self.json_format_dict({}, True)

        node_id = self.index[self.args.host]

        node = self.get_node(node_id)
        instance_vars = {}
        for key in vars(instance):
            value = getattr(instance, key)
            key = self.to_safe('ec2_' + key)

            # Handle complex types
            if type(value) in [int, bool]:
                instance_vars[key] = value
            elif type(value) in [str, unicode]:
                instance_vars[key] = value.strip()
            elif type(value) == type(None):
                instance_vars[key] = ''
            elif key == 'ec2_region':
                instance_vars[key] = value.name
            elif key == 'ec2_tags':
                for k, v in value.iteritems():
                    key = self.to_safe('ec2_tag_' + k)
                    instance_vars[key] = v
            elif key == 'ec2_groups':
                group_ids = []
                group_names = []
                for group in value:
                    group_ids.append(group.id)
                    group_names.append(group.name)
                instance_vars["ec2_security_group_ids"] = ','.join(group_ids)
                instance_vars["ec2_security_group_names"] = ','.join(group_names)
            else:
                pass
                # TODO Product codes if someone finds them useful
                #print key
                #print type(value)
                #print value

        return self.json_format_dict(instance_vars, True)
        
    def push(self, my_dict, key, element):
        '''
        Pushed an element onto an array that may not have been defined in
        the dict
        '''

        if key in my_dict:
            my_dict[key].append(element);
        else:
            my_dict[key] = [element]


    def get_inventory_from_cache(self):
        '''
        Reads the inventory from the cache file and returns it as a JSON
        object
        '''

        cache = open(self.cache_path_cache, 'r')
        json_inventory = cache.read()
        return json_inventory


    def load_index_from_cache(self):
        '''
        Reads the index from the cache file sets self.index
        '''

        cache = open(self.cache_path_index, 'r')
        json_index = cache.read()
        self.index = json.loads(json_index)


    def write_to_cache(self, data, filename):
        '''
        Writes data in JSON format to a file
        '''

        json_data = self.json_format_dict(data, True)
        cache = open(filename, 'w')
        cache.write(json_data)
        cache.close()


    def to_safe(self, word):
        '''
        Converts 'bad' characters in a string to underscores so they can be
        used as Ansible groups
        '''

        return re.sub("[^A-Za-z0-9\-]", "_", word)

    def json_format_dict(self, data, pretty=False):
        '''
        Converts a dict to a JSON object and dumps it as a formatted
        string
        '''

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)

def main():
    clcInventory()
    

if __name__ == '__main__':
	main()