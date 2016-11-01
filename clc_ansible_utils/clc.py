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
    :param method:
    :param url:
    :param headers:
    :param data:
    :return response:
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
    return response


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
        response = call_clc_api(
            module, clc_auth,
            'POST', '/authentication/login',
            data={'username': v2_api_username,
                  'password': v2_api_passwd})
        if response.code not in [200]:
            return module.fail_json(
                msg='Failed to authenticate with clc V2 api.')
        r = json.loads(response.read())
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
