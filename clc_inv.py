#!/usr/bin/env python
# Copyright 2015 CenturyLink
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#    http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
#
#  TODO: Add caching
#  TODO: Add ability to specify AccountAlias

import sys
import os
from multiprocessing import Pool
import itertools
import json
import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException

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
    clc_auth = clc_common.authenticate(None)

    groups = _find_all_groups(clc_auth)
    servers = _get_servers_from_groups(groups)
    hostvars = _find_all_hostvars_for_servers(clc_auth, servers)
    dynamic_groups = _build_hostvars_dynamic_groups(hostvars)
    groups.update(dynamic_groups)

    result = groups
    result['_meta'] = hostvars

    print(json.dumps(result, indent=2, sort_keys=True))


def _find_all_groups(clc_auth):
    '''
    Obtain a list of all datacenters for the account, and then return a list of their Server Groups
    :param clc_auth: dict containing the needed parameters for authentication
    :return: group dictionary
    '''
    datacenters = _filter_datacenters(_find_datacenters(clc_auth))
    results = [_find_groups_for_datacenter(clc_auth, datacenter)
               for datacenter in datacenters]

    # Filter out results with no values
    results = [result for result in results if result]
    return _parse_groups_result_to_dict(results)


def _find_datacenters(clc_auth):
    '''
    Get list of all datacenters for an account
    :param clc_auth: dict containing the needed parameters for authentication
    :return:
    '''
    result = clc_common.call_clc_api(
        None, clc_auth,
        'GET', '/datacenters/{alias}'.format(alias=clc_auth['clc_alias']))
    datacenters = [d['id'] for d in result]
    return datacenters


def _filter_datacenters(datacenters):
    '''
    Return only datacenters that are listed in the CLC_FILTER_DATACENTERS env var
    :param datacenters: a list of datacenters to filter
    :return: a filtered list of datacenters
    '''
    include_datacenters = os.environ.get('CLC_FILTER_DATACENTERS')
    if include_datacenters:
        return [datacenter for datacenter in datacenters if str(
            datacenter).upper() in include_datacenters.upper().split(',')]
    else:
        return datacenters


def _find_groups_for_datacenter(clc_auth, datacenter):
    '''
    Return a dictionary of groups and hosts for the given datacenter
    :param datacenter: The datacenter to use for finding groups
    :return: dictionary of { '<GROUP NAME>': 'hosts': [SERVERS]}
    '''
    result = {}
    root_group = clc_common.group_tree(None, clc_auth, datacenter=datacenter)
    result = _find_all_servers_for_group(clc_auth, datacenter,
                                         root_group.children)
    if result:
        return result


def _find_all_servers_for_group(clc_auth, datacenter, groups):
    '''
    recursively walk down all groups retrieving server information.
    :param datacenter: The datacenter being search.
    :param groups: The current group level which is being searched.
    :return: dictionary of {'<GROUP NAME>': 'hosts': [SERVERS]}
    '''
    result = {}
    for group in groups:
        sub_groups = group.children
        if ( len(sub_groups) > 0 ):
            sub_result = {}
            sub_result = _find_all_servers_for_group(clc_auth, datacenter,
                                                     sub_groups)
            if sub_result is not None:
                result.update( sub_result )

        if group.type != 'default':
            continue

        try:
            servers = [obj['id'] for obj in group.data['links'] if
                       obj['rel'] == 'server']
        except ClcApiException:
            continue  # Skip any groups we can't read.

        if servers:
            result[group.name] = {'hosts': servers}
            result[
                str(datacenter).upper() +
                '_' +
                group.name] = {
                'hosts': servers}

    if result:
        return result


def _find_all_hostvars_for_servers(clc_auth, servers):
    '''
    Return a hostvars dictionary for the provided list of servers.
    Multithreaded to optimize network calls.
    :cvar HOSTVAR_POOL_CNT: The number of threads to use
    :param servers: list of servers to find hostvars for
    :return: dictionary of servers(k) and hostvars(v)
    '''
    p = Pool(HOSTVAR_POOL_CNT)
    arg_list = [(clc_auth, s) for s in servers]
    results = p.map(_find_hostvars_single_server, arg_list)
    p.close()
    p.join()

    hostvars = {}
    for result in results:
        if result is not None:
            hostvars.update(result)

    return {'hostvars': hostvars}


def _find_hostvars_single_server(arg_list):
    '''
    Return dictionary of hostvars for a single server
    :param server_id: the id of the server to query
    :return:
    '''
    result = {}
    clc_auth, server_id = arg_list
    try:
        server = clc_common.find_server(None, clc_auth, server_id)

        if len(server.data['details']['ipAddresses']) == 0:
            return

        result[server.name] = {
            'ansible_ssh_host': server.data['details']['ipAddresses'][0]['internal'],
            'clc_data': server.data,
            'clc_custom_fields': server.data['details']['customFields']
        }
        result = _add_windows_hostvars(result, server)
    except (ClcApiException, KeyError):
        return  # Skip any servers that return bad data or an api exception

    return result

def _add_windows_hostvars(hostvars, server):
    '''
    Add windows specific hostvars if the OS is windows
    :param server_id: the id of the server being checked
    :return: a dictionary of windows specific hostvars
    '''
    if 'windows' in hostvars[server.name]['clc_data']['os']:
        windows_hostvars = {
            'ansible_ssh_port': 5986,
            'ansible_connection': 'winrm'
        }
        hostvars[server.name].update(windows_hostvars)
    return hostvars


def _build_hostvars_dynamic_groups(hostvars):
    '''
    Build a dictionary of dynamically generated groups, parsed from
    the hostvars of each server.
    :param hostvars: hostvars to process
    :return: dictionary of dynamically built groups based on server attributes
    '''
    result = {}
    result.update(_build_datacenter_groups(hostvars=hostvars))
    return result


def _build_datacenter_groups(hostvars):
    '''
    Return a dictionary of groups, one for each datacenter, containing all
    of the servers in that datacenter
    :param hostvars: The hostvars dictionary to parse
    :return: Dictionary of dynamically built Datacenter groups
    '''
    result = {}
    hostvars = hostvars.get('hostvars')
    for server in hostvars:
        datacenter = hostvars[server]['clc_data']['locationId']
        if datacenter not in result:
            result[datacenter] = []
        result[datacenter] += [server]
    return result


def _parse_groups_result_to_dict(lst):
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
    return set(_flatten_list([groups[group]['hosts'] for group in groups]))


def _flatten_list(lst):
    '''
    Flattens a list of lists until at least one value is no longer iterable
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
    result = True if len(lst) == 0 else False 
    i = 0
    while i < len(lst) and not result:
        result |= (
            not isinstance(lst[i], list) and
            not isinstance(lst[i], dict) and
            not isinstance(lst[i], tuple) and
            not isinstance(lst[i], file))
        i += 1
    return result


if __name__ == '__main__':
    main()
