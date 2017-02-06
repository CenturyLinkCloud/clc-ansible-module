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
module: clc_firewall_policy
short_description: Create/delete/update firewall policies
description:
  - Create or delete or update firewall polices on Centurylink Cloud
version_added: "2.0"
options:
  location:
    description:
      - Target datacenter for the firewall policy
    required: True
  state:
    description:
      - Whether to create or delete the firewall policy
    default: present
    required: False
    choices: ['present', 'absent']
  source:
    description:
      - The list  of source addresses for traffic on the originating firewall.
        This is required when state is 'present"
    default: None
    required: False
  destination:
    description:
      - The list of destination addresses for traffic on the terminating firewall.
        This is required when state is 'present'
    default: None
    required: False
  ports:
    description:
      - The list of ports associated with the policy.
        TCP and UDP can take in single ports or port ranges.
    default: None
    required: False
    choices: ['any', 'icmp', 'TCP/123', 'UDP/123', 'TCP/123-456', 'UDP/123-456']
  firewall_policy_id:
    description:
      - Id of the firewall policy. This is required to update or delete an existing firewall policy
    default: None
    required: False
  source_account_alias:
    description:
      - CLC alias for the source account
    required: True
  destination_account_alias:
    description:
      - CLC alias for the destination account
    default: None
    required: False
  wait:
    description:
      - Whether to wait for the provisioning tasks to finish before returning.
    default: True
    required: False
    choices: [True, False]
  enabled:
    description:
      - Whether the firewall policy is enabled or disabled
    default: True
    required: False
    choices: [True, False]
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
---
- name: Create Firewall Policy
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create / Verify an Firewall Policy at CenturyLink Cloud
      clc_firewall:
        source_account_alias: WFAD
        location: VA1
        state: present
        source: 10.128.216.0/24
        destination: 10.128.216.0/24
        ports: Any
        destination_account_alias: WFAD

---
- name: Delete Firewall Policy
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Delete an Firewall Policy at CenturyLink Cloud
      clc_firewall:
        source_account_alias: WFAD
        location: VA1
        state: absent
        firewall_policy_id: 'c62105233d7a4231bd2e91b9c791e43e1'
'''

RETURN = '''
changed:
    description: A flag indicating if any change was made or not
    returned: success
    type: boolean
    sample: True
firewall_policy_id
    description: The fire wall policy id
    returned: success
    type: string
    sample: fc36f1bfd47242e488a9c44346438c05
firewall_policy:
    description: The fire wall policy information
    returned: success
    type: dict
    sample:
        {
           "destination":[
              "10.1.1.0/24",
              "10.2.2.0/24"
           ],
           "destinationAccount":"wfad",
           "enabled":true,
           "id":"fc36f1bfd47242e488a9c44346438c05",
           "links":[
              {
                 "href":"http://api.ctl.io/v2-experimental/firewallPolicies/wfad/uc1/fc36f1bfd47242e488a9c44346438c05",
                 "rel":"self",
                 "verbs":[
                    "GET",
                    "PUT",
                    "DELETE"
                 ]
              }
           ],
           "ports":[
              "any"
           ],
           "source":[
              "10.1.1.0/24",
              "10.2.2.0/24"
           ],
           "status":"active"
        }
'''

__version__ = '${version}'

from future import standard_library
standard_library.install_aliases()
import urllib.parse
from time import sleep

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException


class ClcFirewallPolicy(object):

    def __init__(self, module):
        """
        Construct module
        """
        self.clc_auth = {}
        self.module = module

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            location=dict(required=True),
            source_account_alias=dict(required=True, default=None),
            destination_account_alias=dict(default=None),
            firewall_policy_id=dict(default=None),
            ports=dict(default=None, type='list'),
            source=dict(default=None, type='list'),
            destination=dict(default=None, type='list'),
            wait=dict(default=True),
            state=dict(default='present', choices=['present', 'absent']),
            enabled=dict(default=True, choices=[True, False])
        )
        return argument_spec

    def process_request(self):
        """
        Execute the main code path, and handle the request
        :return: none
        """
        self.clc_auth = clc_common.authenticate(self.module)
        # Firewall operations use v2-experimental, so over-ride default
        self.clc_auth['v2_api_url'] = self.clc_auth['v2_api_url'].replace(
            '/v2', '/v2-experimental', 1)

        changed = False
        firewall_policy = None
        firewall_policy_id = self.module.params.get('firewall_policy_id')
        state = self.module.params.get('state')

        if state == 'absent':
            changed, firewall_policy_id, firewall_policy = \
                self._ensure_firewall_policy_is_absent()

        elif state == 'present':
            changed, firewall_policy_id, firewall_policy = \
                self._ensure_firewall_policy_is_present()

        return self.module.exit_json(
            changed=changed,
            firewall_policy_id=firewall_policy_id,
            firewall_policy=firewall_policy)

    @staticmethod
    def _get_policy_id_from_response(response):
        """
        Method to parse out the policy id from creation response
        :param response: response from firewall creation API call
        :return: policy_id: firewall policy id from creation call
        """
        url = response.get('links')[0]['href']
        path = urllib.parse.urlparse(url).path
        path_list = os.path.split(path)
        policy_id = path_list[-1]
        return policy_id

    def _ensure_firewall_policy_is_present(self):
        """
        Ensures that a given firewall policy is present
        :return: (changed, firewall_policy_id, firewall_policy)
            changed: flag for if a change occurred
            firewall_policy_id: the firewall policy id that was created/updated
            firewall_policy: The firewall_policy object
        """
        p = self.module.params
        firewall_policy_id = p.get('firewall_policy_id')

        changed = False
        firewall_policy = None

        if firewall_policy_id is not None:
            # Search for the firewall policy
            firewall_policy = self._get_firewall_policy(firewall_policy_id)
            if firewall_policy is None:
                return self.module.fail_json(
                    msg='Unable to find the firewall policy id: {id}'.format(
                        id=firewall_policy_id))
        if firewall_policy is None:
            changed = True
            if not self.module.check_mode:
                response = self._create_firewall_policy()
                firewall_policy_id = self._get_policy_id_from_response(
                    response)
        elif self._policy_update_needed(firewall_policy):
            changed = True
            if not self.module.check_mode:
                self._update_firewall_policy(firewall_policy)

        if changed and firewall_policy_id:
            firewall_policy = self._wait_for_requests_to_complete(
                firewall_policy_id)

        return changed, firewall_policy_id, firewall_policy

    def _ensure_firewall_policy_is_absent(self):
        """
        Ensures that a given firewall policy is removed if present
        :return: (changed, firewall_policy_id, response)
            changed: flag for if a change occurred
            firewall_policy_id: the firewall policy id that was deleted
            response: response from CLC API call
        """
        p = self.module.params
        firewall_policy_id = p.get('firewall_policy_id')

        changed = False
        response = None
        firewall_policy = self._get_firewall_policy(firewall_policy_id)
        if firewall_policy:
            changed = True
            if not self.module.check_mode:
                response = self._delete_firewall_policy(firewall_policy)
        return changed, firewall_policy_id, response

    def _create_firewall_policy(self):
        """
        Creates the firewall policy for the given account alias
        :return: response from CLC API call
        """
        p = self.module.params
        source_account_alias = p.get('source_account_alias')
        location = p.get('location')

        payload = {
            'destinationAccount': p.get('destination_account_alias'),
            'source': p.get('source'),
            'destination': p.get('destination'),
            'ports': p.get('ports')
            }
        try:
            response = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'POST', '/firewallPolicies/{alias}/{location}'.format(
                    alias=source_account_alias, location=location),
                data=payload)
        except ClcApiException as e:
            return self.module.fail_json(
                msg='Unable to create firewall policy for alias: {alias} '
                    'in location: {location}. {msg}'.format(
                        alias=source_account_alias, location=location,
                        msg=e.message))

        return response

    def _delete_firewall_policy(self, policy):
        """
        Deletes a given firewall policy for an account alias in a datacenter
        :param policy: firewall policy to delete
        :return: response: response from CLC API call
        """
        p = self.module.params
        source_account_alias = p.get('source_account_alias')
        location = p.get('location')

        try:
            # Returns 204 No Content
            response = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'DELETE', '/firewallPolicies/{alias}/{location}/{id}'.format(
                    alias=source_account_alias, location=location,
                    id=policy['id']))
        except ClcApiException as e:
            return self.module.fail_json(
                msg='Unable to delete the firewall policy id: {id}. '
                    '{msg}'.format(id=policy['id'], msg=e.message))

        return response

    def _update_firewall_policy(self, policy):
        """
        Updates a firewall policy for a given datacenter and account alias
        :param policy: firewall policy to update
        :return: response: response from CLC API call
        """
        p = self.module.params
        source_account_alias = p.get('source_account_alias')
        location = p.get('location')

        enabled = (p.get('enabled') or policy['enabled'])
        source = (p.get('source') or policy['source'])
        destination = (p.get('destination') or policy['destination'])
        ports = (p.get('ports') or policy['ports'])

        payload = {
            'enabled': enabled,
            'source': source,
            'destination': destination,
            'ports': ports
        }
        try:
            # Returns 204 No Response
            response = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'PUT', '/firewallPolicies/{alias}/{location}/{id}'.format(
                    alias=source_account_alias, location=location,
                    id=policy['id']),
                data=payload)
        except ClcApiException as e:
            return self.module.fail_json(
                msg='Unable to update the firewall policy id: {id}. '
                    '{msg}'.format(id=policy['id'], msg=e.message))

        return response

    def _policy_update_needed(self, policy):
        """
        Helper method to determine whether an updated is required by comparing
        the policy returned from the CLC API and the module parameters
        :param policy: Policy to compare to module parameters
        :return: changed: Boolean, True if a difference is found
        """
        p = self.module.params

        dest_alias = p.get('destination_account_alias')
        enabled = p.get('enabled')
        source = p.get('source')
        destination = p.get('destination')
        ports = p.get('ports')

        changed = False

        if dest_alias and dest_alias != policy['destinationAccount']:
            self.module.fail_json(
                msg='Changing destination alias from: {orig} to: {new} '
                    'is not supported.'.format(
                      orig=policy['destinationAccount'], new=dest_alias))
        if (enabled != policy['enabled']
                or source and source != policy['source']
                or destination and destination != policy['destination']
                or ports and ports != policy['ports']):
            changed = True

        return changed

    def _firewall_policies(self, source_alias, location):
        try:
            policies = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'GET', '/firewallPolicies/{alias}/{location}'.format(
                    alias=source_alias, location=location))
        except ClcApiException as e:
            return self.module.fail_json(
                msg='Unable to fetch firewall policies for alias: {alias} '
                    'in location: {location}. {msg}'.format(
                        alias=source_alias, location=location,
                        msg=e.message))
        return policies

    def _get_firewall_policy(self, firewall_policy_id,
                             source_account_alias=None, location=None):
        """
        Get back details for a particular firewall policy
        :param firewall_policy_id: id of the firewall policy to get
        :param source_account_alias: source account alias for firewall policy
        :param location: datacenter of the firewall policy
        :return: response - The response from CLC API call
        """
        p = self.module.params
        alias = (source_account_alias or p.get('source_account_alias'))
        location = (location or p.get('location'))

        policies = self._firewall_policies(alias, location)
        policies = [p for p in policies if p['id'] == firewall_policy_id]

        return policies[0] if len(policies) > 0 else None

    def _wait_for_requests_to_complete(self, firewall_policy_id,
                                       wait_limit=50, poll_freq=2):
        """
        Waits until the CLC requests are complete if the wait argument is True
        :param firewall_policy_id: The firewall policy id
        :param wait_limit: number of times to check the status for completion
        :return: the firewall_policy object
        """
        p = self.module.params
        wait = p.get('wait')

        count = 0
        firewall_policy = None
        while wait:
            count += 1
            firewall_policy = self._get_firewall_policy(firewall_policy_id)
            status = firewall_policy.get('status')
            if status == 'active' or count > wait_limit:
                wait = False
            else:
                # wait for 2 seconds
                sleep(poll_freq)
        return firewall_policy


def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
        argument_spec=ClcFirewallPolicy._define_module_argument_spec(),
        supports_check_mode=True)

    clc_firewall = ClcFirewallPolicy(module)
    clc_firewall.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
