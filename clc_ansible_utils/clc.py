#!/usr/bin/env python
# -*- coding: utf-8 -*-

# CenturyLink Cloud Ansible Modules.
#
# These Ansible modules enable the CenturyLink Cloud v2 API to be called
# from an within Ansible Playbook.
#
# This file is part of CenturyLink Cloud, and is maintained
# by the Workflow as a Service Team
#
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
#
# CenturyLink Cloud: http://www.CenturyLinkCloud.com
# API Documentation: https://www.centurylinkcloud.com/api-docs/v2/
#

__version__ = '${version}'

import os
import json
import math
import urllib
import urllib2

from ansible.module_utils.basic import *  # pylint: disable=W0614
from ansible.module_utils.urls import *  # pylint: disable=W0614


class ClcApiException(Exception):

    def __init__(self, message=None, code=None):
        if message is not None:
            super(self.__class__, self).__init__(message)
        else:
            super(self.__class__, self).__init__()
        self.code = code


class Group(object):

    def __init__(self, group_data):
        self.alias = None
        self.id = None
        self.name = None
        self.description = None
        self.parent = None
        self.children = []
        if group_data is not None:
            self.data = group_data
            for attr in ['id', 'name', 'description', 'type']:
                if attr in group_data:
                    setattr(self, attr, group_data[attr])


class Server(object):

    def __init__(self, server_data):
        self.id = None
        self.name = None
        self.description = None
        if server_data is not None:
            self.data = server_data
            for attr in ['id', 'name', 'description', 'status', 'powerState',
                         'locationId', 'groupId']:
                if attr in server_data:
                    setattr(self, attr, server_data[attr])
                elif ('details' in server_data and
                        attr in server_data['details']):
                    setattr(self, attr, server_data['details'][attr])
            try:
                self.data['details']['memoryGB'] = int(
                    math.floor(self.data['details']['memoryMB']/1024))
            except:
                pass


class Network(object):

    def __init__(self, network_data):
        self.id = None
        self.name = None
        self.cidr = None
        self.description = None
        self.type = None
        if network_data is not None:
            self.data = network_data
            for attr in ['id', 'name', 'description', 'type',
                         'cidr', 'gateway', 'netmask']:
                if attr in network_data:
                    setattr(self, attr, network_data[attr])


def _default_headers():
    # Helpful ansible open_url params
    # data, headers, http-agent
    headers = {}
    agent_string = 'ClcAnsibleModule/' + __version__
    headers['Api-Client'] = agent_string
    headers['User-Agent'] = 'Python-urllib2/{version} {agent}'.format(
         version=urllib2.__version__, agent=agent_string)
    return headers


def call_clc_api(module, clc_auth, method, url, headers=None, data=None):
    """
    Make a request to the CLC API v2.0
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param method: HTTP method
    :param url: URL string to be appended to root api_url
    :param headers: Headers to be added to request
    :param data: Data to be sent with request
    :return response: HTTP response from urllib2.urlopen
    """
    if not isinstance(url, str) or not isinstance(url, basestring):
        raise TypeError('URL for API request must be a string')
    if headers is None:
        headers = _default_headers()
    elif not isinstance(headers, dict):
        raise TypeError('Headers for API request must be a dict')
    else:
        headers = _default_headers().update(headers)
    if data is not None and not isinstance(data, (dict, list)):
        raise TypeError('Data for API request must be JSON Serrializable')
    # Obtain Bearer token if we do not already have it
    if 'authentication/login' not in url:
        if 'v2_api_token' not in clc_auth:
            clc_auth = authenticate(module)
        headers['Authorization'] = 'Bearer {token}'.format(
            token=clc_auth['v2_api_token'])
    if data is not None:
        if method.upper() == 'GET':
            url += '?' + urllib.urlencode(data)
            data = None
        else:
            data = json.dumps(data)
            headers['Content-Type'] = 'application/json'
    try:
        response = open_url(
            url='{endpoint}/{path}'.format(
                endpoint=clc_auth['v2_api_url'].rstrip('/'),
                path=url.lstrip('/')),
            method=method,
            headers=headers,
            data=data)
    except urllib2.HTTPError as ex:
        api_ex = ClcApiException(
            message='Error calling CenturyLink Cloud API: {msg}'.format(
                msg=ex.reason),
            code=ex.code)
        raise api_ex
    except ssl.SSLError as ex:
        raise ex
    try:
        return json.loads(response.read())
    except:
        raise ClcApiException(
            'Error converting CenturyLink Cloud API response to JSON')


def operation_status(module, clc_auth, operation_id):
    """
    Call back to the CLC API to determine status
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param operation_id: Operation id for which to check the status
    :return: Status of the operation, one of the below values
    ('notStarted, 'executing', 'succeeded', 'failed', 'resumed', 'unknown')
    """
    response = call_clc_api(
        module, clc_auth,
        'GET', '/operations/{alias}/status/{id}'.format(
            alias=clc_auth['clc_alias'], id=operation_id))
    return response['status']


def operation_id_list(response_data):
    """
    Extract list of operation IDs from CLC API response
    :param response_data: JSON data from API response. A list of dicts.
    :return: List of operation IDs.
    """
    operation_ids = []
    for operation in response_data:
        # Operation ID format returned as part server operations
        if isinstance(operation, list):
            # Call recursively if response is a list of operations
            operation_ids.extend(operation_id_list(operation))
        elif 'links' in operation:
            operation_ids.extend([o['id'] for o in operation['links']
                                  if o['rel'] == 'status'])
        elif 'rel' in operation and operation['rel'] == 'status':
            operation_ids.extend([operation['id']])
        # Operation ID format returned as part of network operations
        elif 'operationId' in operation:
            operation_ids.extend([operation['operationId']])
    return operation_ids


def wait_on_completed_operations(module, clc_auth, operation_ids):
    """
    Wait for list of operations to complete
    :param module:
    :param clc_auth:
    :param operation_ids:
    :return:
    """
    ops_succeeded = []
    ops_failed = []
    for operation_id in operation_ids:
        try:
            _wait_until_complete(module, clc_auth, operation_id)
            ops_succeeded.append(operation_id)
        except ClcApiException:
            ops_failed.append(operation_id)
    return len(ops_failed)


def _wait_until_complete(module, clc_auth, operation_id, poll_freq=2):
    """
    Wail until CLC API operation is complete
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param operation_id: Operation id for which to wait for completion
    :param poll_freq: How frequently to poll the CLC API
    :return:
    """
    time_completed = None
    while not time_completed:
        status = operation_status(module, clc_auth, operation_id)
        if status == 'succeeded':
            time_completed = time.time()
        elif status == 'failed':
            time_completed = time.time()
            raise ClcApiException(
                'Execution of operation {id} {status}'.format(
                    id=operation_id, status=status))
        else:
            time.sleep(poll_freq)


def authenticate(module):
    """
    Authenticate against the CLC V2 API
    :param module: Ansible module being called
    :return: clc_auth - dict containing the needed parameters for authentication
    """
    v2_api_url = 'https://api.ctl.io/v2/'
    env = os.environ
    v2_api_token = env.get('CLC_V2_API_TOKEN', False)
    v2_api_username = env.get('CLC_V2_API_USERNAME', False)
    v2_api_passwd = env.get('CLC_V2_API_PASSWD', False)
    clc_alias = env.get('CLC_ACCT_ALIAS', False)
    clc_location = env.get('CLC_LOCATION', False)
    v2_api_url = env.get('CLC_V2_API_URL', v2_api_url)
    clc_auth = {'v2_api_url': v2_api_url}
    # Populate clc_auth, authenticating if needed
    if v2_api_token and clc_alias and clc_location:
        clc_auth.update({
            'v2_api_token': v2_api_token,
            'clc_alias': clc_alias,
            'clc_location': clc_location,
        })
    elif v2_api_username and v2_api_passwd:
        r = call_clc_api(
            module, clc_auth,
            'POST', '/authentication/login',
            data={'username': v2_api_username,
                  'password': v2_api_passwd})
        clc_auth.update({
            'v2_api_token': r['bearerToken'],
            'clc_alias': r['accountAlias'],
            'clc_location': r['locationAlias']
        })
    else:
        return module.fail_json(
            msg='You set the CLC_V2_API_USERNAME and '
                'CLC_V2_API_PASSWD environment variables')
    return clc_auth


def _walk_groups(parent_group, group_data):
    """
    Walk a parent-child tree of groups, starting with the provided child group
    :param parent_group: Group - Parent of group described by group_data
    :param group_data: dict - Dict of data from JSON API return
    :return: Group object from data, containing list of children
    """
    group = Group(group_data)
    group.parent = parent_group
    for child_data in group_data['groups']:
        if child_data['type'] != 'default':
            continue
        group.children.append(_walk_groups(group, child_data))
    return group


def group_tree(module, clc_auth, alias=None, datacenter=None):
    """
    Walk the tree of groups for a datacenter
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param datacenter: string - the datacenter to walk (ex: 'UC1')
    :return: Group object for root group containing list of children
    """
    if datacenter is None:
        datacenter = clc_auth['clc_location']
    if alias is None:
        alias = clc_auth['clc_alias']
    r = call_clc_api(
        module, clc_auth,
        'GET', '/datacenters/{alias}/{location}'.format(
            alias=alias, location=datacenter),
        data={'GroupLinks': 'true'})

    root_group_id, root_group_name = [(obj['id'], obj['name'])
                                      for obj in r['links']
                                      if obj['rel'] == "group"][0]

    group_data = call_clc_api(
        module, clc_auth,
        'GET', '/groups/{alias}/{id}'.format(
            alias=alias, id=root_group_id))

    return _walk_groups(None, group_data)


def _find_group_recursive(search_group, group_info, parent_info=None):
    """
    :param search_group: Group under which to search
    :param group_info: Name or id of group to search for
    :param parent_info: Optional name or id of parent
    :return: List of groups found matching the described parameters
    """
    groups = []
    if group_info.lower() in [search_group.id.lower(),
                              search_group.name.lower()]:
        if parent_info is None:
            groups.append(search_group)
        elif (search_group.parent is not None and
                parent_info.lower() in [search_group.parent.id.lower(),
                                        search_group.parent.name.lower()]):
            groups.append(search_group)
    for child_group in search_group.children:
        groups += _find_group_recursive(child_group, group_info,
                                        parent_info=parent_info)
    return groups


def find_group(module, search_group, group_info, parent_info=None):
    """
    :param module: Ansible module being called
    :param search_group: Group under which to search
    :param group_info: Name or id of group to search for
    :param parent_info:  Optional name or id of parent
    :return: Group object found, or None if no groups found.
    Will return an error if multiple groups found matching parameters.
    """
    groups = _find_group_recursive(
        search_group, group_info, parent_info=parent_info)
    if len(groups) > 1:
        error_message = 'Found {num:d} groups with name: \"{name}\"'.format(
            num=len(groups), name=group_info)
        if parent_info is None:
            error_message += ', no parent group specified.'
        else:
            error_message += ' in group: \"{name}\".'.format(
                name=parent_info)
        error_message += ' Group ids: ' + ', '.join([g.id for g in groups])
        return module.fail_json(msg=error_message)
    elif len(groups) == 1:
        return groups[0]
    else:
        return None


def group_path(group, group_id=False, delimiter='/'):
    """
    :param group: Group object for which to show full ancestry
    :param group_id: Optional flag to show group id hierarchy
    :param delimiter: Optional delimiter
    :return:
    """
    path_elements = []
    while group is not None:
        if group_id:
            path_elements.append(group.id)
        else:
            path_elements.append(group.name)
        group = group.parent
    return delimiter.join(reversed(path_elements))


def networks_in_datacenter(module, clc_auth, datacenter):
    """
    Return list of networks in datacenter
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param datacenter: the datacenter to search for a network id
    :return: A list of Network objects
    """
    networks = []
    if 'clc_location' not in clc_auth:
        clc_auth = authenticate(module)

    try:
        temp_auth = clc_auth.copy()
        temp_auth['v2_api_url'] = 'https://api.ctl.io/v2-experimental/'
        response = call_clc_api(
            module, temp_auth,
            'GET', '/networks/{alias}/{location}'.format(
                alias=temp_auth['clc_alias'], location=datacenter))
        networks = [Network(n) for n in response]
        return networks
    except ClcApiException:
        return module.fail_json(
            msg=str(
                "Unable to find a network in location: " +
                datacenter))


def find_network(module, clc_auth, datacenter,
                 network_id_search=None, networks=None):
    """
    Validate the provided network id or return a default.
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param datacenter: the datacenter to search for a network id
    :param network_id_search: Network id for which to search for
    :param networks: List of networks in which to search. If None, call API.
    :return: A valid Network object
    """
    network_found = None
    # Validates provided network id
    # Allows lookup of network by id, name, or cidr notation
    if not networks:
        networks = networks_in_datacenter(module, clc_auth, datacenter)

    if network_id_search:
        for network in networks:
            if network_id_search.lower() in [network.id.lower(),
                                             network.name.lower(),
                                             network.cidr.lower()]:
                network_found = network
                break
    else:
        network_found = networks[0]
    return network_found


def find_server(module, clc_auth, server_id):
    """
    Find server information based on server_id
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param server_id: ID for server for which to retrieve data
    :return: Server object
    """
    try:
        r = call_clc_api(
            module, clc_auth,
            'GET', 'servers/{alias}/{id}'.format(
                alias=clc_auth['clc_alias'], id=server_id))
        server = Server(r)
        return server
    except ClcApiException as ex:
        return module.fail_json(
            msg='Failed to get server information '
                'for server id: {id}:'.format(id=server_id))


def servers_by_id(module, clc_auth, server_ids):
    """
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param server_ids: list of server IDs for which to retrieve data
    :return: List of server objects containing information from API Calls
    """
    servers = []
    for server_id in server_ids:
        servers.append(find_server(module, clc_auth, server_id))
    return servers


def servers_in_group(module, clc_auth, group):
    """
    Return a list of servers from
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param group: Group object to search for servers
    :return: List of server objects containing information from API Calls
    """
    server_lst = [obj['id'] for obj in group.data['links'] if
                  obj['rel'] == 'server']
    return servers_by_id(module, clc_auth, server_lst)
