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

DOCUMENTATION = '''
module: clc_server_fact
short_description: Get facts about servers in CenturyLink Cloud.
description:
  - An Ansible module to retrieve facts about servers in CenturyLink Cloud.
version_added: "2.2"
options:
  server_id:
    description:
      - The server id to retrieve facts for.
    required: True
  credentials:
    description:
      - Indicates if server credentials should be returned in the facts.
    required: False
    default: False
    choices: [False, True]
requirements:
    - python = 2.7
author: "CLC Runner (@clc-runner)"
notes:
    - To use this module, it is required to set the below environment variables which enables access to the
      Centurylink Cloud
          - CLC_V2_API_USERNAME, the account login id for the centurylink cloud
          - CLC_V2_API_PASSWORD, the account password for the centurylink cloud
    - Alternatively, the module accepts the API token and account alias. The API token can be generated using the
      CLC account login and password via the HTTP api call @ https://api.ctl.io/v2/authentication/login
          - CLC_V2_API_TOKEN, the API token generated from https://api.ctl.io/v2/authentication/login
          - CLC_ACCT_ALIAS, the account alias associated with the centurylink cloud
    - Users can set CLC_V2_API_URL to specify an endpoint for pointing to a different CLC environment.
'''

EXAMPLES = '''
# Note - You must set the CLC_V2_API_USERNAME And CLC_V2_API_PASSWD Environment variables before running these examples

- name: Retrieve Server Facts
  clc_server_fact:
    server_id: UC1WFADWRDPRS10

- name: Retrieve Server Facts With Credentials
  clc_server_fact:
    server_id: UC1WFADWRDPRS10
    credentials: true

'''

RETURN = '''
changed:
    description: A flag indicating if any change was made or not
    returned: success
    type: boolean
    sample: True
server:
    description: The retrieved server facts.
    returned: success
    type: dict
    sample:
        "server": {
                "changeInfo": {
                    "createdBy": "chris.kent.wfad",
                    "createdDate": "2016-03-15T19:44:40Z",
                    "modifiedDate": "2016-03-15T19:47:46Z"
                },
                "description": "WRDPRS",
                "details": {
                    "alertPolicies": [],
                    "cpu": 1,
                    "customFields": [],
                    "diskCount": 3,
                    "disks": [
                        {
                            "id": "0:0",
                            "partitionPaths": [],
                            "sizeGB": 1
                        },
                        {
                            "id": "0:1",
                            "partitionPaths": [],
                            "sizeGB": 2
                        },
                        {
                            "id": "0:2",
                            "partitionPaths": [],
                            "sizeGB": 14
                        }
                    ],
                    "hostName": "uc1wfadwrdprs10",
                    "inMaintenanceMode": false,
                    "ipAddresses": [
                        {
                            "internal": "10.100.121.210",
                            "public": "206.152.34.248"
                        }

                    ],
                    "memoryMB": 2048,
                    "partitions": [
                        {
                            "path": "(swap)",
                            "sizeGB": 0.0
                        },
                        {
                            "path": "/",
                            "sizeGB": 13.655
                        },
                        {
                            "path": "/boot",
                            "sizeGB": 0.474
                        }
                    ],
                    "powerState": "started",
                    "secondaryIPAddresses": [],
                    "snapshots": [],
                    "storageGB": 17
                },
                "displayName": "UC1WFADWRDPRS10",
                "groupId": "0e330aec1d2f46cfbf77b5b06d50e733",
                "id": "uc1wfadwrdprs10",
                "ipaddress": "10.100.121.210",
                "isTemplate": false,
                "links": [
                    {
                        "href": "/v2/servers/wfad/uc1wfadwrdprs10",
                        "id": "uc1wfadwrdprs10",
                        "rel": "self",
                        "verbs": [
                            "GET",
                            "PATCH",
                            "DELETE"
                        ]
                    },
                    {
                        "href": "/v2/groups/wfad/0e330aec1d2f46cfbf77b5b06d50e733",
                        "id": "0e330aec1d2f46cfbf77b5b06d50e733",
                        "rel": "group"
                    },
                    {
                        "href": "/v2/accounts/wfad",
                        "id": "wfad",
                        "rel": "account"
                    },
                    {
                        "href": "/v2/billing/wfad/serverPricing/uc1wfadwrdprs10",
                        "rel": "billing"
                    },
                    {
                        "href": "/v2/servers/wfad/uc1wfadwrdprs10/publicIPAddresses",
                        "rel": "publicIPAddresses",
                        "verbs": [
                            "POST"
                        ]
                    },
                    {
                        "href": "/v2/servers/wfad/uc1wfadwrdprs10/credentials",
                        "rel": "credentials"
                    },
                    {
                        "href": "/v2/servers/wfad/uc1wfadwrdprs10/statistics",
                        "rel": "statistics"
                    },
                    {
                        "href": "/v2/servers/wfad/e3561ed15320456e9890561df7be6e19/upcomingScheduledActivities",
                        "rel": "upcomingScheduledActivities"
                    },
                    {
                        "href": "/v2/servers/wfad/e3561ed15320456e9890561df7be6e19/scheduledActivities",
                        "rel": "scheduledActivities",
                        "verbs": [
                            "GET",
                            "POST"
                        ]
                    },
                    {
                        "href": "/v2/servers/wfad/uc1wfadwrdprs10/capabilities",
                        "rel": "capabilities"
                    },
                    {
                        "href": "/v2/servers/wfad/uc1wfadwrdprs10/alertPolicies",
                        "rel": "alertPolicyMappings",
                        "verbs": [
                            "POST"
                        ]
                    },
                    {
                        "href": "/v2/servers/wfad/uc1wfadwrdprs10/antiAffinityPolicy",
                        "rel": "antiAffinityPolicyMapping",
                        "verbs": [
                            "PUT",
                            "DELETE"
                        ]
                    },
                    {
                        "href": "/v2/servers/wfad/uc1wfadwrdprs10/cpuAutoscalePolicy",
                        "rel": "cpuAutoscalePolicyMapping",
                        "verbs": [
                            "PUT",
                            "DELETE"
                        ]
                    }
                ],
                "locationId": "UC1",
                "name": "UC1WFADWRDPRS10",
                "os": "ubuntu14_64Bit",
                "osType": "Ubuntu 14 64-bit",
                "publicip": "206.152.34.248",
                "status": "active",
                "storageType": "standard",
                "type": "standard"
            }
'''

__version__ = '${version}'

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException


class ClcServerFact(object):

    def __init__(self, module):
        """
        Construct module
        """
        self.clc_auth = {}
        self.module = module

    def process_request(self):
        """
        Process the request - Main Code Path
        :return: Returns with either an exit_json or fail_json
        """
        server_id = self.module.params.get('server_id')

        self.clc_auth = clc_common.authenticate(self.module)

        server = clc_common.find_server(self.module, self.clc_auth, server_id)
        server = clc_common.server_ip_addresses(self.module, self.clc_auth,
                                                server)

        if self.module.params.get('credentials'):
            server.data['credentials'] = self._get_server_credentials(server_id)

        self.module.exit_json(changed=False, server=server.data)

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            server_id=dict(required=True),
            credentials=dict(default=False))

        return {"argument_spec": argument_spec}

    def _get_server_credentials(self, server_id):
        """
        Retrieve login credentials for server
        :return: credentials for server with server_id
        """
        try:
            response = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'GET', '/servers/{alias}/{id}/credentials'.format(
                    alias=self.clc_auth['clc_alias'], id=server_id))
        except ClcApiException as e:
            return self.module.fail_json(
                msg='Unable to fetch the credentials for server id: {id}. '
                    '{msg}'.format(
                        id=server_id, msg=e.message))
        return response


def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    argument_dict = ClcServerFact._define_module_argument_spec()
    module = AnsibleModule(supports_check_mode=True, **argument_dict)
    clc_server_fact = ClcServerFact(module)
    clc_server_fact.process_request()

from ansible.module_utils.basic import * # pylint: disable=W0614
if __name__ == '__main__':
    main()
