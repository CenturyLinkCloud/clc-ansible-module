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

import clc_ansible_utils.clc as clc_common


class ClcLoadbalancerFact(object):

    def __init__(self, module):
        """
        Build module
        """
        self.clc_auth = {}
        self.module = module

    def process_request(self):
        """
        Process the request - Main Code Path
        :return: Returns with either an exist_json or fail_json
        """
        name = self.module.params.get('name')
        location = self.module.params.get('location')
        alias = self.module.params.get('alias')

        self.clc_auth = clc_common.authenticate(self.module)

        loadbalancer = clc_common.find_loadbalancer(
            self.module, self.clc_auth, name,
            alias=alias, location=location)

        if loadbalancer is None:
            return self.module.fail_json(
                msg='Load balancer with name: {name} does not exist '
                    'for account: {alias} at location: {location}.'.format(
                        name=name, alias=alias, location=location))

        self.module.exit_json(changed=False, loadbalancer=loadbalancer)

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionaries
        """
        return {"argument_spec": dict(name=dict(required=True),
                                      location=dict(required=True),
                                      alias=dict(required=True))}


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
