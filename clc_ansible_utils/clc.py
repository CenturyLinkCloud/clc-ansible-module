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
import urllib

from ansible.module_utils.basic import *  # pylint: disable=W0614
from ansible.module_utils.urls import *  # pylint: disable=W0614


class ClcApiException(Exception):
    pass


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
            for attr in ['id', 'name', 'description', 'status',
                         'locationId', 'groupId']:
                if attr in server_data:
                    setattr(self, attr, server_data[attr])


def _default_headers():
    # Helpful ansible open_url params
    # data, headers, http-agent
    headers = {}
    agent_string = 'ClcAnsibleModule/' + __version__
    headers['Api-Client'] = agent_string
    headers['User-Agent'] = 'Python-urllib2/{0} {1}'.format(
         urllib2.__version__, agent_string)
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
    if data is not None and not isinstance(data, dict):
        raise TypeError('Data for API request must be a dict')
    # Obtain Bearer token if we do not already have it
    if 'authentication/login' not in url:
        if 'v2_api_token' not in clc_auth:
            clc_auth = authenticate(module)
        headers['Authorization'] = 'Bearer {0}'.format(clc_auth['v2_api_token'])
    if data is not None:
        if method.upper() == 'GET':
            url += '?' + urllib.urlencode(data)
            data = None
        else:
            data = json.dumps(data)
            headers['Content-Type'] = 'application/json'
    try:
        response = open_url(
            url='{0}/{1}'.format(clc_auth['v2_api_url'].rstrip('/'),
                                 url.lstrip('/')),
            method=method,
            headers=headers,
            data=data)
    except urllib2.HTTPError as ex:
        raise ClcApiException(
            'Error calling CenturyLink Cloud API: {0}'.format(ex.message))
    try:
        return json.loads(response.read())
    except:
        raise ClcApiException(
            'Error converting CenturyLink Cloud API response to JSON')


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
        'GET', '/datacenters/{0}/{1}'.format(
            alias, datacenter),
        data={'GroupLinks': 'true'})

    root_group_id, root_group_name = [(obj['id'], obj['name'])
                                      for obj in r['links']
                                      if obj['rel'] == "group"][0]

    group_data = call_clc_api(
        module, clc_auth,
        'GET', '/groups/{0}/{1}'.format(
            alias, root_group_id))

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
                parent_info in [search_group.parent.id,
                                search_group.parent.name]):
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
        error_message = 'Found {0:d} groups with name: \"{1}\"'.format(
            len(groups), group_info)
        if parent_info is None:
            error_message += ', no parent group specified.'
        else:
            error_message += ' in group: \"{0}\".'.format(parent_info)
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


def _find_server(module, clc_auth, server_id):
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
            'GET', 'servers/{0}/{1}'.format(
                clc_auth['clc_alias'], server_id))
        server = Server(r)
        return server
    except ClcApiException as ex:
        return module.fail_json(
            msg='Failed to get server information '
                'for server id: {0}:'.format(server_id))


def servers_in_group(module, clc_auth, group):
    """
    Return a list of servers from
    :param module:
    :param clc_auth:
    :param group:
    :return:
    """
    server_lst = [obj['id'] for obj in group.data['links'] if
                  obj['rel'] == 'server']
    servers = []
    for server_id in server_lst:
        servers.append(_find_server(module, clc_auth, server_id))
    return servers
