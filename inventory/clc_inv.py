#!/usr/bin/python

'''
CenturyLink Cloud dynamic inventory script
==========================================

This script returns an inventory to Ansible by making calls to the
clc-sdk Python SDK.

NOTE:  This script assumes that environment variables are already set
with control portal credentials in the format of:

    export CLC_V2_API_USERNAME=<your Control Portal Username>
    export CLC_V2_API_PASSWD=<your Control Portal Password>

These credentials are required to use the CLC API and must be provided.

This script returns all information about hosts in the inventory _meta dictionary.

The following information is returned for each host:
    - ansible_ssh_host:  Set to the first internal ip address
    - clc_custom_fields:  A dictionary of custom fields set on the server in the Control Portal
    - clc_data:  A dictionary of all the data returned by the API
'''

#  @author: Brian Albrecht

import sys
import os
from multiprocessing import Pool
import itertools
import json
import clc
from clc import CLCException

GROUP_POOL_CNT = 10
HOSTVAR_POOL_CNT = 25

def main():
    '''
    Main function
    :return: None
    '''
    print_inventory_json()
    sys.exit(0)

def print_inventory_json():
    '''
    Print the inventory in json.  This is the main execution path for the script
    :return: None
    '''
    _set_clc_credentials_from_env()

    groups = _find_all_groups()
    servers = _get_servers_from_groups(groups)
    hostvars = _find_all_hostvars_for_servers(servers)

    result = groups
    result['_meta'] = hostvars

    print json.dumps(result)

def _find_all_groups():
    '''
    Obtain a list of all datacenters for the account, and then return a list of their Server Groups
    Multithreaded to optimize network calls.
    :cvar GROUP_POOL_CNT:  The number of processes to use.
    :return: group dictionary
    '''
    p = Pool(GROUP_POOL_CNT)
    datacenters = clc.v2.Datacenter().Datacenters()
    results = p.map(_find_groups_for_datacenter, datacenters)
    p.close()
    p.join()
    results = [result for result in results if result]  # Filter out results with no values
    return _parse_groups_results_to_dict(results)

def _find_groups_for_datacenter(datacenter):
    '''
    Return a dictionary of groups and hosts for the given datacenter
    :param datacenter: The datacenter use for finding groups
    :return: dictionary of { '<GROUP NAME>': 'hosts': [SERVERS]}
    '''
    groups = datacenter.Groups().groups
    result = {}
    for group in groups:
        try:
            servers = group.Servers().servers_lst
        except CLCException:
            continue  # Skip any groups we can't read.

        if servers:
            result[group.name] = {'hosts': servers}

    if result:
        return result

def _find_all_hostvars_for_servers(servers):
    '''
    Return a hostvars dictionary for the provided list of servers.
    Multithreaded to optimize network calls.
    :cvar HOSTVAR_POOL_CNT: The number of threads to use
    :param servers: list of servers to find hostvars for
    :return: dictionary of servers(k) and hostvars(v)
    '''
    p = Pool(HOSTVAR_POOL_CNT)
    results = p.map(_find_hostvars_for_single_server, servers)
    p.close()
    p.join()

    hostvars = {}
    for result in results:
        if result is not None:
            hostvars.update(result)

    return {'hostvars': hostvars}

def _find_hostvars_for_single_server(server_id):
    '''
    Return dictionary of hostvars for a single server
    :param server_id: the id of the server to query
    :return:
    '''
    result = {}
    try:
        server = clc.v2.Server(server_id)

        result[server.name] = {
            'ansible_ssh_host': server.data['details']['ipAddresses'][0]['internal'],
            'clc_data': server.data,
            'clc_custom_fields': server.data['details']['customFields']
        }
    except CLCException, KeyError:
        return  # Skip any servers that return bad data or an api exception

    return result

def _parse_groups_results_to_dict(lst):
    '''
    Return a parsed list of groups that can be converted to Ansible Inventory JSON
    :param lst: list of group results to parse
    :return: dictionary of groups and hosts { '<GROUP NAME>': 'hosts': [SERVERS]}
    '''
    result = {}
    for groups in sorted(lst):
        for group in groups:
            if group not in result:
                result[group] = {'hosts': []}
            result[group]['hosts'] += _flatten_list(groups[group]['hosts'])
    return result

def _get_servers_from_groups(groups):
    '''
    Return a flat list of servers for the provided dictionary of groups
    :param groups: dictionary of groups to parse
    :return: flat list of servers ['SERVER1','SERVER2', etc]
    '''
    return _flatten_list([groups[group]['hosts'] for group in groups])

def _flatten_list(lst):
    '''
    Flattens a list of lists until at least one value is not iterable
    :param lst: list to flatten
    :return: flattened list
    '''
    while not _is_list_flat(lst):
        lst = list(itertools.chain.from_iterable(lst))
    return lst

def _is_list_flat(lst):
    '''
    Checks to see if the list contains any values that are not iterable.
    :param lst: list to check
    :return: True if any value in the list is not an iterable
    '''
    result = False
    i = 0
    while i < len(lst) and not result:
        result |= (
            type(lst[i]) is not list and
            type(lst[i]) is not dict and
            type(lst[i]) is not tuple and
            type(lst[i]) is not file)
        i += 1
    return result

def _set_clc_credentials_from_env():
    '''
    Set the v2 API Credentials on the clc-sdk from environment variables.  Uses an API Token if set
    otherwise, uses USERNAME and PASSWORD.
    :return: None
    '''
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

if __name__ == '__main__':
    main()
