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
        pass

    def process_inventory(self):
        ''' Main execution path '''

        # Inventory grouped by instance IDs, tags, security groups, regions,
        # and availability zones
        self.inventory = {}

        # Index of hostname (address) to instance ID
        self.index = {}

        # Read settings and parse CLI arguments
        self.read_settings()
        self.parse_cli_args()
        self.get_clc_credentials_from_env()

        # Cache
        if self.args.refresh_cache:
            self.do_api_calls_update_cache()
        elif not self.is_cache_valid():
            self.do_api_calls_update_cache()

        # Data to print
        if self.args.host:
            data_to_print = json_format_Dict([], True)

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
        clc_default_ini_path = os.path.join(
            os.path.dirname(
                os.path.realpath(__file__)),
            'clc_settings.ini')
        clc_ini_path = os.environ.get('CLC_INI_PATH', clc_default_ini_path)
        config.read(clc_ini_path)

        # Cache related
        cache_path = config.get('cache', 'cache_path')
        self.cache_path_cache = cache_path + "/ansible-clc.cache"
        self.cache_path_index = cache_path + "/ansible-clc.index"
        self.cache_max_age = config.getint('cache', 'cache_max_age')

    def get_clc_credentials_from_env(self):
        env = os.environ
        v2_api_token = env.get('CLC_V2_API_TOKEN', False)
        v2_api_username = env.get('CLC_V2_API_USERNAME', False)
        v2_api_passwd = env.get('CLC_V2_API_PASSWD', False)

        if v2_api_token:
            clc._LOGIN_TOKEN_V2 = v2_api_token
        elif v2_api_username and v2_api_passwd:
            clc.v2.SetCredentials(
                api_username=v2_api_username,
                api_passwd=v2_api_passwd)

    def parse_cli_args(self):
        '''
        Command line argument processing
        '''

        parser = argparse.ArgumentParser(
            description='Produce an Ansible Inventory file based from CenturyLink Cloud servers and groups')
        parser.add_argument('--list', action='store_true', default=True,
                            help='List instances (default: True)')
        parser.add_argument(
            '--host',
            action='store',
            help='Get all the variables about a specific instance')
        parser.add_argument(
            '--refresh-cache',
            action='store_true',
            default=False,
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

        groups = self._get_groups_for_datacenter()

        for group in groups:
            child, parent = groups[group]
            try:
                servers = child.Servers().servers
            except clc.CLCException, e:
                if 'Server does not exist' in e.message:
                    return

            for node in servers:
                self.add_node(node.data)

        self.write_to_cache(self.inventory, self.cache_path_cache)
        self.write_to_cache(self.index, self.cache_path_index)

    def get_node(self, node_id):
        '''
        Gets details about a specific node
        '''

        return clc.v2.Server(node_id)

    def add_node(self, node):
        '''
        Adds a node to the inventory and index, as long as it is
        addressable
        '''

        # Only want running instances
        if node['details']['powerState'] != "started":
            return

        # Select the best destination address
        for address in node['details']['ipAddresses']:
            if 'internal' in address:
                dest = address['internal']
                break
        if not dest:
            # Skip instances we cannot address (e.g. private VPC subnet)
            return

        # Add to index
        self.index[dest] = node['name']

        # Inventory: Group by instance ID (always a group of 1)
        self.inventory[node['name']] = [dest]
        '''
        # Inventory: Group by region
        self.push(self.inventory, region, dest)

        # Inventory: Group by availability zone
        self.push(self.inventory, node.placement, dest)

        # Inventory: Group by instance type
        self.push(self.inventory, self.to_safe('type_' + node.instance_type), dest)
        '''

        # Inventory: Group by security group, quick thing to handle single sg
        if node['groupId']:
            self.push(
                self.inventory,
                self.to_safe(
                    self.group_name_from_UUID(
                        node['groupId'])),
                dest)

    def group_name_from_UUID(self, uuid):
        return str(clc.v2.Group(id=uuid))

    def push(self, my_dict, key, element):
        '''
        Pushed an element onto an array that may not have been defined in
        the dict
        '''

        if key in my_dict:
            my_dict[key].append(element)
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

    def _get_groups_for_datacenter(self, datacenter=None, alias=None):
        root_group = clc.v2.Datacenter(location=datacenter).RootGroup()
        return self._walk_groups_recursive(parent_group=None, child_group=root_group)

    def _walk_groups_recursive(self, parent_group, child_group):
        result = {str(child_group): (child_group, parent_group)}
        groups = child_group.Subgroups().groups
        if len(groups) > 0:
            for group in groups:
                result.update(self._walk_groups_recursive(child_group, group))
        return result


def main():
    clc_inventory = clcInventory()
    clc_inventory.process_inventory()

if __name__ == '__main__':
    main()
