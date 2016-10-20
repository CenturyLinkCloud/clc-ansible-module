#!/usr/bin/env python

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

DOCUMENTATION = '''
module: clc_loadbalancer_fact
short_description: Get facts about loadbalancers in the Centurylink Cloud
description:
  - An Ansible module to retrieve facts about loadbalancers in the Centurylink Cloud
version_added: "2.0"
options:
  name:
    - The name of the loadbalancer to gather data
  location:
    description:
      - The datacenter the loadbalancer is based
    required: True
    default: False
    example: UC1
requirements:
  - python = 2.7
  - requests >= 2.5.0
author: "CLC Runner (@clc-runner)"
notes:
  - To use this module, it is required to set the below environmental variables which enable access to CLC
      - CLC_V2_API_USERNAME: the account login id for CLC
      - CLC_V2_API_PASSWORD: the password for the CLC account
  - Alternatively, the module accepts the API token and account alias. The API token can be generated using the CLC
    account login and password via the HTTP api call @ https://api.ctl.io/v2/authentication/login
      - CLC_V2_API_TOKEN: the API token generated from https://api.ctl.io/v2/authentication/login
      - CLC_ACCT_ALIAS: the account alias associated with CLC
  - Users can set CLC_V2_API_URL to specify an endpoint for pointing to a different CLC environment
'''

EXAMPLES = '''
# NOTE - You must set the CLC_V2_API_USERNAME and CLC_V2_API_PASSWD Environmental variables before running examples

- name: Retrieve loadbalancer facts
  clc_loadbalancer_fact:
    name: TEST
    location: UC1
    alias: WFTC
  register: loadbalancer
'''

RETURN = '''
changed:
  description: a flag indicating if any change was made or not
  returned: success
  type: boolean
  sample: True
loadbalancer:
  description: The retrieved loadbalancer info
  returned: success
  type: dict
  sample:
    "loadbalancer": {
        "changed": false,
        "loadbalancer": {
            "description": "Test VIP",
            "id": "d95075012d3b462fb711960b4cfa534a",
            "ipAddress": "206.152.35.15",
            "links": [
                {
                    "href": "/v2/sharedLoadBalancers/wfti/ca3/d95075012d3b462fb711960b4cfa534a",
                    "rel": "self",
                    "verbs": [
                        "GET",
                        "PUT",
                        "DELETE"
                    ]
                },
                {
                    "href": "/v2/sharedLoadBalancers/wfti/ca3/d95075012d3b462fb711960b4cfa534a/pools",
                    "rel": "pools",
                    "verbs": [
                        "GET",
                        "POST"
                    ]
                }
            ],
            "name": "TEST",
            "pools": [
                {
                    "id": "2b725058801c421ca97945ff4146d081",
                    "links": [
                        {
                            "href": "/v2/sharedLoadBalancers/wfti/ca3/d95075012d3b462fb711960b4cfa534a/pools/2b725058801c421ca97945ff4146d081",
                            "rel": "self",
                            "verbs": [
                                "GET",
                                "PUT",
                                "DELETE"
                            ]
                        },
                        {
                            "href": "/v2/sharedLoadBalancers/wfti/ca3/d95075012d3b462fb711960b4cfa534a/pools/2b725058801c421ca97945ff4146d081/nodes",
                            "rel": "nodes",
                            "verbs": [
                                "GET",
                                "PUT"
                            ]
                        }
                    ],
                    "method": "roundRobin",
                    "nodes": [
                        {
                            "ipAddress": "10.101.168.13",
                            "privatePort": 8443,
                            "status": "enabled"
                        },
                        {
                            "ipAddress": "10.101.168.14",
                            "privatePort": 8443,
                            "status": "enabled"
                        }
                    ],
                    "persistence": "standard",
                    "port": 443
                }
            ],
            "status": "enabled"
        }
    }
}
'''

__version__ = '{version}'

from distutils.version import LooseVersion

try:
    import requests
except ImportError:
    REQUESTS_FOUND = False
else:
    REQUESTS_FOUND = True

try:
    import clc as clc_sdk
    from clc import APIFailedResponse
except ImportError:
    CLC_FOUND = False
    clc_sdk = None
else:
    CLC_FOUND = True


class ClcLoadbalancerFact(object):

    def __init__(self, module):
        """
        Build module
        """
        self.clc = clc_sdk
        self.module = module
        self.lb_dict = {}

        if not CLC_FOUND:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')
        if not REQUESTS_FOUND:
            self.module.fail_json(
                msg='requests library is required for this module')
        if requests.__version__ and LooseVersion(
                requests.__version__) < LooseVersion('2.5.0'):
            self.module.fail_json(
                msg='requests library  version should be >= 2.5.0')

    def process_request(self):
        """
        Process the request - Main Code Path
        :return: Returns with either an exist_json or fail_json
        """
        self._set_clc_credentials_from_env()
        name = self.module.params.get('name')
        location = self.module.params.get('location')
        alias = self.module.params.get('alias')
        result = None

        self.lb_dict = self._get_loadbalancer_list(
            alias=alias,
            location=location)

        try:
            result = self._get_endpoint(alias, location, name)
        except APIFailedResponse as e:
            self.module.fail_json(msg=e.response_text)

        self.module.exit_json(changed=False, loadbalancer=result)

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionaries
        """
        return {"argument_spec": dict(name=dict(required=True),
                                      location=dict(required=True),
                                      alias=dict(required=True))}

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
        api_url = env.get('CLC_V2_API_URL', False)

        if api_url:
            self.clc.defaults.ENDPOINT_URL_V2 = api_url

        if v2_api_token and clc_alias:
            self.clc._LOGIN_TOKEN_V2 = v2_api_token
            self.clc._V2_ENABLED = True
            self.clc.ALIAS = clc_alias
        elif v2_api_username and v2_api_passwd:
            self.clc.v2.SetCredentials(
                api_username=v2_api_username,
                api_passwd=v2_api_passwd)
        else:
            return self.module.fail_json(
                msg="You must set the CLC_V2_API_USERNAME and CLC_V2_API_PASSWD "
                    "environment variables")

    def _get_loadbalancer_list(self, alias, location):
        """
        Retrieve a list of loadbalancers
        :param alias: Alias for account
        :param location: Datacenter
        :return: JSON data for all loadbalancers at location
        """
        result = None
        try:
            result = self.clc.v2.API.Call(
                'GET', '/v2/sharedLoadBalancers/%s/%s' % (alias, location))
        except APIFailedResponse as e:
            self.module.fail_json(
                msg='Unable to fetch load balancers for account: {0} at location: {1}. {2}'.format(
                    alias, location, str(e.message)))
        return result

    def _get_loadbalancer_id(self, name):
        """
        Retrieves unique ID of loadbalancer
        :param name: Name of loadbalancer
        :return: Unique ID of the loadbalancer
        """
        lb_id = None
        for lb in self.lb_dict:
            if lb.get('name') == name:
                lb_id = lb.get('id')
        return lb_id

    def _get_endpoint(self, alias, location, name):
        lb_id = self._get_loadbalancer_id(name=name)
        if not lb_id:
            self.module.fail_json(
                msg='load balancer {0} does not exist for account: {1} at location: {2}'.format(
                    name, alias, location
                )
            )
        try:
            return self.clc.v2.API.Call(
                'GET', '/v2/sharedLoadBalancers/%s/%s/%s' % (alias, location, lb_id))
        except APIFailedResponse as e:
            self.module.fail_json(
                msg='Unable to get information for load balancer {0} with account: {1} at location: {2}. {3}'.format(
                    name, alias, location, str(e.message)))



def main():
    """
    The main function. Instantiates the module and calls process_request
    :return: none
    """
    argument_dict = ClcLoadbalancerFact._define_module_argument_spec()
    module = AnsibleModule(supports_check_mode=True, **argument_dict)
    clc_loadbalancer_fact = ClcLoadbalancerFact(module)
    clc_loadbalancer_fact.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
