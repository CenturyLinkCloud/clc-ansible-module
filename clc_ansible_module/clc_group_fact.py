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
module: clc_group_fact
short_description: Get facts about groups in CenturyLink Cloud.
description:
  - An Ansible module to retrieve facts about groups in CenturyLink Cloud.
version_added: "2.0"
options:
  group_id:
    description:
      - The group id to retrieve facts for.
    required: True
requirements:
    - python = 2.7
    - requests >= 2.5.0
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

- name: Retrieve Group Facts
  clc_group_fact:
    group_id: 31d13f501459411ba59304f3d47486eb

'''

RETURN = '''
changed:
    description: A flag indicating if any change was made or not
    returned: success
    type: boolean
    sample: True
server:
    description: The retrieved group facts.
    returned: success
    type: dict
    sample:
        "group": {
                "changeInfo": {
                    "createdBy": "mark.ramach.wfas",
                    "createdDate": "2016-04-07T23:37:15Z",
                    "modifiedBy": "mark.ramach.wfas",
                    "modifiedDate": "2016-04-07T23:37:15Z"
                },
                "customFields": [],
                "description": "K8S",
                "groups": [],
                "id": "479857c65d6a42d8b2523fab58c4c3cb",
                "links": [
                    {
                        "href": "/v2/groups/wfad",
                        "rel": "createGroup",
                        "verbs": [
                            "POST"
                        ]
                    },
                    {
                        "href": "/v2/servers/wfad",
                        "rel": "createServer",
                        "verbs": [
                            "POST"
                        ]
                    },
                    {
                        "href": "/v2/groups/wfad/479857c65d6a42d8b2523fab58c4c3cb",
                        "rel": "self",
                        "verbs": [
                            "GET",
                            "PATCH",
                            "DELETE"
                        ]
                    },
                    {
                        "href": "/v2/groups/wfad/a319873a32e84c17aa76306a477b9a22",
                        "id": "a319873a32e84c17aa76306a477b9a22",
                        "rel": "parentGroup"
                    },
                    {
                        "href": "/v2/groups/wfad/479857c65d6a42d8b2523fab58c4c3cb/defaults",
                        "rel": "defaults",
                        "verbs": [
                            "GET",
                            "POST"
                        ]
                    },
                    {
                        "href": "/v2/groups/wfad/479857c65d6a42d8b2523fab58c4c3cb/billing",
                        "rel": "billing"
                    },
                    {
                        "href": "/v2/groups/wfad/479857c65d6a42d8b2523fab58c4c3cb/archive",
                        "rel": "archiveGroupAction"
                    },
                    {
                        "href": "/v2/groups/wfad/479857c65d6a42d8b2523fab58c4c3cb/statistics",
                        "rel": "statistics"
                    },
                    {
                        "href": "/v2/groups/wfad/479857c65d6a42d8b2523fab58c4c3cb/upcomingScheduledActivities",
                        "rel": "upcomingScheduledActivities"
                    },
                    {
                        "href": "/v2/groups/wfad/479857c65d6a42d8b2523fab58c4c3cb/horizontalAutoscalePolicy",
                        "rel": "horizontalAutoscalePolicyMapping",
                        "verbs": [
                            "GET",
                            "PUT",
                            "DELETE"
                        ]
                    },
                    {
                        "href": "/v2/groups/wfad/479857c65d6a42d8b2523fab58c4c3cb/scheduledActivities",
                        "rel": "scheduledActivities",
                        "verbs": [
                            "GET",
                            "POST"
                        ]
                    },
                    {
                        "href": "/v2/servers/wfad/uc1wfadk8sm16",
                        "id": "UC1WFADK8SM16",
                        "rel": "server"
                    },
                    {
                        "href": "/v2/servers/wfad/uc1wfadk8sn46",
                        "id": "UC1WFADK8SN46",
                        "rel": "server"
                    },
                    {
                        "href": "/v2/servers/wfad/uc1wfadk8sm17",
                        "id": "UC1WFADK8SM17",
                        "rel": "server"
                    },
                    {
                        "href": "/v2/servers/wfad/uc1wfadk8sn45",
                        "id": "UC1WFADK8SN45",
                        "rel": "server"
                    }
                ],
                "locationId": "UC1",
                "name": "K8S",
                "servers": [
                    "UC1WFADK8SM16",
                    "UC1WFADK8SN46",
                    "UC1WFADK8SM17",
                    "UC1WFADK8SN45"
                ],
                "serversCount": 4,
                "status": "active",
                "type": "default"
            }
        }
'''

__version__ = '${version}'

try:
    import requests
except ImportError:
    REQUESTS_FOUND = False
else:
    REQUESTS_FOUND = True


class ClcGroupFact(object):

    def __init__(self, module):
        """
        Construct module
        """
        self.module = module

        if not REQUESTS_FOUND:
            self.module.fail_json(
                msg='requests library is required for this module')

    def process_request(self):
        """
        Process the request - Main Code Path
        :return: Returns with either an exit_json or fail_json
        """
        self._set_clc_credentials_from_env()
        group_id = self.module.params.get('group_id')

        r = requests.get(self._get_endpoint(group_id), headers={
            'Authorization': 'Bearer ' + self.v2_api_token
        })

        if r.status_code not in [200]:
            self.module.fail_json(
                msg='Failed to retrieve group facts: %s' %
                group_id)

        r = r.json()
        servers = r['servers'] = []

        for l in r['links']:
            if 'server' == l['rel']:
                servers.append(l['id'])

        self.module.exit_json(changed=False, group=r)

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        return {"argument_spec": dict(group_id=dict(required=True))}

    def _get_endpoint(self, group_id):
        return self.api_url + '/v2/groups/' + self.clc_alias + '/' + group_id

    def _set_clc_credentials_from_env(self):
        """
        Set the CLC Credentials by reading environment variables
        :return: none
        """
        env = os.environ
        v2_api_token = env.get('CLC_V2_API_TOKEN', False)
        v2_api_username = env.get('CLC_V2_API_USERNAME', False)
        v2_api_passwd = env.get('CLC_V2_API_PASSWD', False)
        clc_alias = env.get('CLC_ACCT_ALIAS', False)
        self.api_url = env.get('CLC_V2_API_URL', 'https://api.ctl.io')

        if v2_api_token and clc_alias:

            self.v2_api_token = v2_api_token
            self.clc_alias = clc_alias

        elif v2_api_username and v2_api_passwd:

            r = requests.post(self.api_url + '/v2/authentication/login', json={
                'username': v2_api_username,
                'password': v2_api_passwd
            })

            if r.status_code not in [200]:
                self.module.fail_json(
                    msg='Failed to authenticate with clc V2 api.')

            r = r.json()
            self.v2_api_token = r['bearerToken']
            self.clc_alias = r['accountAlias']

        else:
            return self.module.fail_json(
                msg="You must set the CLC_V2_API_USERNAME and CLC_V2_API_PASSWD "
                    "environment variables")


def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    argument_dict = ClcGroupFact._define_module_argument_spec()
    module = AnsibleModule(supports_check_mode=True, **argument_dict)
    clc_group_fact = ClcGroupFact(module)
    clc_group_fact.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
