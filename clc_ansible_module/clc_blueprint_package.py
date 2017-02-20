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
module: clc_blueprint_package
short_description: deploys a blue print package on a set of servers in CenturyLink Cloud.
description:
  - An Ansible module to deploy blue print package on a set of servers in CenturyLink Cloud.
version_added: "2.0"
options:
  server_ids:
    description:
      - A list of server Ids to deploy the blue print package.
    required: True
  package_id:
    description:
      - The package id of the blue print.
    required: True
  package_params:
    description:
      - The dictionary of arguments required to deploy the blue print.
    default: {}
    required: False
  state:
    description:
      - Whether to install or un-install the package. Currently it supports only "present" for install action.
    required: False
    default: present
    choices: ['present']
  wait:
    description:
      - Whether to wait for the tasks to finish before returning.
    choices: [ True, False ]
    default: True
    required: False
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

- name: Deploy package
      clc_blueprint_package:
        server_ids:
            - UC1TEST-SERVER1
            - UC1TEST-SERVER2
        package_id: 77abb844-579d-478d-3955-c69ab4a7ba1a
        package_params: {}
'''

RETURN = '''
changed:
    description: A flag indicating if any change was made or not
    returned: success
    type: boolean
    sample: True
server_ids:
    description: The list of server ids that are changed
    returned: success
    type: list
    sample:
        [
            "UC1TEST-SERVER1",
            "UC1TEST-SERVER2"
        ]
'''

__version__ = '${version}'

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException


class ClcBlueprintPackage(object):

    module = None

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
        self.clc_auth = clc_common.authenticate(self.module)
        p = self.module.params
        changed = False
        changed_server_ids = []
        server_ids = p['server_ids']
        package_id = p['package_id']
        package_params = p['package_params']
        state = p['state']
        if state == 'present':
            changed, changed_server_ids, request_list = self.ensure_package_installed(
                server_ids, package_id, package_params)
            self._wait_for_requests_to_complete(request_list)
        self.module.exit_json(changed=changed, server_ids=changed_server_ids)

    @staticmethod
    def define_argument_spec():
        """
        This function defines the dictionary object required for
        package module
        :return: the package dictionary object
        """
        argument_spec = dict(
            server_ids=dict(type='list', required=True),
            package_id=dict(type='str', required=True),
            package_params=dict(type='dict', default={}),
            wait=dict(type='bool', default=True),
            state=dict(type='str', default='present',
                       choices=['present'])
        )
        return argument_spec

    def ensure_package_installed(self, server_ids, package_id, package_params):
        """
        Ensure the package is installed in the given list of servers
        :param server_ids: the server list where the package should be installed
        :param package_id: the blueprint package id
        :param package_params: the package arguments
        :return: (changed, server_ids, request_list)
                    changed: A flag indicating if a change was made
                    server_ids: The list of servers modified
                    request_list: The list of request objects from clc-sdk
        """
        changed = False
        request_list = []
        servers = clc_common.servers_by_id(
            self.module, self.clc_auth, server_ids)
        for server in servers:
            if not self.module.check_mode:
                request = self.clc_install_package(
                    server,
                    package_id,
                    package_params)
                request_list.append(request)
            changed = True
        return changed, server_ids, request_list

    def clc_install_package(self, server, package_id, package_params):
        """
        Install the package to a given clc server
        :param server: The server object where the package needs to be installed
        :param package_id: The blue print package id
        :param package_params: the required argument dict for blueprint
        :return: The result object from the CLC API call
        """
        result = None
        payload = {'servers': [server.id],
                   'package': {'packageId': package_id}}
        if package_params:
            payload['package']['parameters'] = package_params
        try:
            result = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'POST', '/operations/{alias}/servers/executePackage'.format(
                    alias=self.clc_auth['clc_alias']),
                data=payload,
                timeout=30)
        except ClcApiException as ex:
            return self.module.fail_json(
                msg='Failed to install package: {pkg} to server {server}. '
                    '{msg}'.format(
                        pkg=package_id, server=server.id, msg=ex.message))
        return result

    def _wait_for_requests_to_complete(self, request_lst):
        """
        Block until server provisioning requests are completed.
        :param request_lst: a list of CLC API JSON responses
        :return: none
        """
        if self.module.params.get('wait'):
            failed_requests_count = clc_common.wait_on_completed_operations(
                self.module, self.clc_auth,
                clc_common.operation_id_list(request_lst))

            if failed_requests_count > 0:
                self.module.fail_json(msg='Unable to process blueprint request')


def main():
    """
    Main function
    :return: None
    """
    module = AnsibleModule(
        argument_spec=ClcBlueprintPackage.define_argument_spec(),
        supports_check_mode=True
    )
    clc_blueprint_package = ClcBlueprintPackage(module)
    clc_blueprint_package.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
