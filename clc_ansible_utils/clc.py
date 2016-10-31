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


class ApiV2(object):

    def __init__(self, module):
        self.module = module
        self._headers = {}
        self._set_user_agent()
        self._default_api_url = 'https://api.ctl.io'

    def _set_user_agent(self):
        # Helpful ansible open_url params
        # data, headers, http-agent
        agent_string = 'ClcAnsibleModule/' + __version__
        self._headers['Api-Client'] = agent_string
        self._headers['User-Agent'] = 'Python-urllib2/{0} {1}'.format(
            urllib2.__version__, agent_string)

    def _set_clc_credentials_from_env(self):
        """
        Set the CLC Credentials on the sdk by reading environment variables
        :return: none
        """
        env = os.environ
        v2_api_token = env.get('CLC_V2_API_TOKEN', False)
        v2_api_username = env.get('CLC_V2_API_USERNAME', False)
        v2_api_passwd = env.get('CLC_V2_API_PASSWD', False)
        clc_alias = env.get('CLC_ACCT_ALIAS', False)
        self.api_url = env.get('CLC_V2_API_URL', self._default_api_url)

        if v2_api_token and clc_alias:
            self.v2_api_token = v2_api_token
            self.clc_alias = clc_alias
        elif v2_api_username and v2_api_passwd:
            response = self.call(
                'POST', '/v2/authentication/login',
                data={'username': v2_api_username,
                      'password': v2_api_passwd})
            if response.code not in [200]:
                return self.module.fail_json(
                    msg='Failed to authenticate with clc V2 api.')

            r = json.loads(response.read())
            self.v2_api_token = r['bearerToken']
            self.clc_alias = r['accountAlias']
            self.clc_location = r['locationAlias']
        else:
            return self.module.fail_json(
                msg='You must set the CLC_V2_API_USERNAME and '
                    'CLC_V2_API_PASSWD environment variables')

    def call(self, method, url, headers=None, data=None):
        """
        Make a request to the CLC API v2.0
        :param method:
        :param url:
        :param headers:
        :param data:
        :return response:
        """
        supported_methods = ('GET', 'POST', 'CREATE', 'UPDATE', 'DELETE')
        if method not in supported_methods:
            raise ValueError('Request method "{0}" not supported'.format(
                method))
        if not isinstance(url, str) or not isinstance(url, basestring):
            raise TypeError('URL for API request must be a string')
        if headers is None:
            headers = self._headers
        if not isinstance(headers, dict):
            raise TypeError('Headers for API request must be a dict')
        if data is not None and not isinstance(data, dict):
            raise TypeError('Data for API request must be a dict')
        # Obtain Bearer token if we do not already have it
        if 'authentication/login' not in url:
            if not hasattr(self, 'v2_api_token') or not self.v2_api_token:
                self._set_clc_credentials_from_env()
            headers['Authorization'] = 'Bearer {0}'.format(self.v2_api_token)
        if data is not None:
            if method.upper() == 'GET':
                url += '?' + urllib.urlencode(data)
                data = None
            else:
                data = json.dumps(data)
                headers['Content-Type'] = 'application/json'
        try:
            response = open_url(url='{0}/{1}'.format(self.api_url,
                                                     url.lstrip('/')),
                                method=method, headers=headers, data=data)
        except urllib2.HTTPError as ex:
            raise

        return response


class Group(object):

    def __init__(self):
        self.alias = None
        self.id = None
        self.name = None
        self.description = None
        self.parent = None
        self.children = []
