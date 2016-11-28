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
from builtins import str
import clc
from clc import CLCException, APIFailedResponse

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
    dynamic_groups = _build_hostvars_dynamic_groups(hostvars)
    groups.update(dynamic_groups)

    result = groups
    result['_meta'] = hostvars

    print(json.dumps(result, indent=2, sort_keys=True))


def _find_all_groups():
    '''
    Obtain a list of all datacenters for the account, and then return a list of their Server Groups
    :return: group dictionary
    '''
    datacenters = _filter_datacenters(clc.v2.Datacenter.Datacenters())
    results = [_find_groups_for_datacenter(datacenter) for datacenter in datacenters]

    # Filter out results with no values
    results = [result for result in results if result]
    return _parse_groups_result_to_dict(results)


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


def _find_groups_for_datacenter(datacenter):
    '''
    Return a dictionary of groups and hosts for the given datacenter
    :param datacenter: The datacenter to use for finding groups
    :return: dictionary of { '<GROUP NAME>': 'hosts': [SERVERS]}
    '''
    result = {}
    groups = datacenter.Groups().groups
    result = _find_all_servers_for_group( datacenter, groups )
    if result:
        return result

def _find_all_servers_for_group( datacenter, groups):
    '''
    recursively walk down all groups retrieving server information.
    :param datacenter: The datacenter being search.
    :param groups: The current group level which is being searched.
    :return: dictionary of {'<GROUP NAME>': 'hosts': [SERVERS]}
    '''
    result = {}
    for group in groups:
        sub_groups = group.Subgroups().groups
        if ( len(sub_groups) > 0 ):
            sub_result = {}
            sub_result = _find_all_servers_for_group( datacenter, sub_groups )
            if sub_result is not None:
                result.update( sub_result )

        if group.type != 'default':
            continue

        try:
            servers = group.Servers().servers_lst
        except CLCException:
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


def _find_all_hostvars_for_servers(servers):
    '''
    Return a hostvars dictionary for the provided list of servers.
    Multithreaded to optimize network calls.
    :cvar HOSTVAR_POOL_CNT: The number of threads to use
    :param servers: list of servers to find hostvars for
    :return: dictionary of servers(k) and hostvars(v)
    '''
    p = Pool(HOSTVAR_POOL_CNT)
    results = p.map(_find_hostvars_single_server, servers)
    p.close()
    p.join()

    hostvars = {}
    for result in results:
        if result is not None:
            hostvars.update(result)

    return {'hostvars': hostvars}


def _find_hostvars_single_server(server_id):
    '''
    Return dictionary of hostvars for a single server
    :param server_id: the id of the server to query
    :return:
    '''
    result = {}
    try:
        session = clc.requests.Session()

        server_obj = clc.v2.API.Call(method='GET',
                                     url='servers/{0}/{1}'.format(clc.ALIAS, server_id),
                                     payload={},
                                     session=session)

        server = clc.v2.Server(id=server_id, server_obj=server_obj)

        if len(server.data['details']['ipAddresses']) == 0:
            return

        result[server.name] = {
            'ansible_ssh_host': server.data['details']['ipAddresses'][0]['internal'],
            'clc_data': server.data,
            'clc_custom_fields': server.data['details']['customFields']
        }
        result = _add_windows_hostvars(result, server)
    except (CLCException, APIFailedResponse, KeyError):
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
    clc_alias = env.get('CLC_ACCT_ALIAS', False)
    api_url = env.get('CLC_V2_API_URL', False)

    if api_url:
        clc.defaults.ENDPOINT_URL_V2 = api_url

    if v2_api_token and clc_alias:
        clc._LOGIN_TOKEN_V2 = v2_api_token
        clc._V2_ENABLED = True
        clc.ALIAS = clc_alias
    elif v2_api_username and v2_api_passwd:
        clc.v2.SetCredentials(
            api_username=v2_api_username,
            api_passwd=v2_api_passwd)
    else:
        sys.stderr.write(
            "\n\nYou must set the CLC_V2_API_USERNAME and CLC_V2_API_PASSWD environment variables to use the CenturyLink Cloud dynamic inventory script.\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
