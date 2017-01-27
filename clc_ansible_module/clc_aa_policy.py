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

DOCUMENTATION = '''
module: clc_aa_policy
short_description: Create or Delete Anti Affinity Policies at CenturyLink Cloud.
description:
  - An Ansible module to Create or Delete Anti Affinity Policies at CenturyLink Cloud.
version_added: "2.0"
options:
  name:
    description:
      - The name of the Anti Affinity Policy.
    required: True
  location:
    description:
      - Datacenter in which the policy lives/should live.
    required: True
  state:
    description:
      - Whether to create or delete the policy.
    required: False
    default: present
    choices: ['present','absent']
  wait:
    description:
      - Whether to wait for the tasks to finish before returning.
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
# Note - You must set the CLC_V2_API_USERNAME And CLC_V2_API_PASSWD Environment variables before running these examples

---
- name: Create AA Policy
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create an Anti Affinity Policy
      clc_aa_policy:
        name: 'Hammer Time'
        location: 'UK3'
        state: present
      register: policy

    - name: debug
      debug: var=policy

---
- name: Delete AA Policy
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Delete an Anti Affinity Policy
      clc_aa_policy:
        name: 'Hammer Time'
        location: 'UK3'
        state: absent
      register: policy

    - name: debug
      debug: var=policy
'''

RETURN = '''
changed:
    description: A flag indicating if any change was made or not
    returned: success
    type: boolean
    sample: True
policy:
    description: The anti affinity policy information
    returned: success
    type: dict
    sample:
        {
           "id":"1a28dd0988984d87b9cd61fa8da15424",
           "name":"test_aa_policy",
           "location":"UC1",
           "links":[
              {
                 "rel":"self",
                 "href":"/v2/antiAffinityPolicies/wfad/1a28dd0988984d87b9cd61fa8da15424",
                 "verbs":[
                    "GET",
                    "DELETE",
                    "PUT"
                 ]
              },
              {
                 "rel":"location",
                 "href":"/v2/datacenters/wfad/UC1",
                 "id":"uc1",
                 "name":"UC1 - US West (Santa Clara)"
              }
           ]
        }
'''

__version__ = '${version}'

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException


class ClcAntiAffinityPolicy(object):

    module = None

    def __init__(self, module):
        """
        Construct module
        """
        self.clc_auth = {}
        self.module = module
        self.policy_dict = {}

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            name=dict(required=True),
            location=dict(required=True),
            wait=dict(default=True),
            state=dict(default='present', choices=['present', 'absent']),
        )
        return argument_spec

    # Module Behavior Goodness
    def process_request(self):
        """
        Process the request - Main Code Path
        :return: Returns with either an exit_json or fail_json
        """
        p = self.module.params

        self.clc_auth = clc_common.authenticate(self.module)

        if p['state'] == "absent":
            changed, policy = self._ensure_policy_is_absent()
        else:
            changed, policy = self._ensure_policy_is_present()

        self.module.exit_json(changed=changed, policy=policy)

    def _create_policy(self):
        """
        Create an Anti Affinity Policy using the CLC API.
        :return: response dictionary from the CLC API.
        """
        try:
            policy = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'POST', '/antiAffinityPolicies/{alias}'.format(
                    alias=self.clc_auth['clc_alias']),
                data={'name': self.module.params['name'],
                      'location': self.module.params['location']})
        except ClcApiException as e:
            return self.module.fail_json(
                msg='Failed to create anti affinity policy: {name}. '
                    '{msg}'.format(name=policy['name'], msg=e.message))
        policy['servers'] = []
        return policy

    def _delete_policy(self, policy):
        """
        Delete an Anti Affinity Policy using the CLC API.
        :param policy: Policy to delete datacenter to delete a policy from
        :return: none
        """

        try:
            # Returns 204 No Content
            response = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'DELETE', '/antiAffinityPolicies/{alias}/{id}'.format(
                    alias=self.clc_auth['clc_alias'], id=policy['id']))
        except ClcApiException as e:
            return self.module.fail_json(
                msg='Failed to delete anti affinity policy: {name}. '
                    '{msg}'.format(name=policy['name'], msg=e.message))

    def _ensure_policy_is_absent(self):
        """
        Makes sure that a policy is absent
        :return: tuple of if a deletion occurred and the name of the policy that was deleted
        """
        p = self.module.params
        changed = False
        policy = clc_common.find_anti_affinity_policy(
            self.module, self.clc_auth, p['name'], location=p['location'])
        if policy:
            changed = True
            if not self.module.check_mode:
                self._delete_policy(policy)
        return changed, None

    def _ensure_policy_is_present(self):
        """
        Ensures that a policy is present
        :return: tuple of if an addition occurred and the name of the policy that was added
        """
        p = self.module.params
        changed = False
        policy = clc_common.find_anti_affinity_policy(
            self.module, self.clc_auth, p['name'], location=p['location'])
        if not policy:
            changed = True
            policy = None
            if not self.module.check_mode:
                policy = self._create_policy()
        return changed, policy


def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
        argument_spec=ClcAntiAffinityPolicy._define_module_argument_spec(),
        supports_check_mode=True)
    clc_aa_policy = ClcAntiAffinityPolicy(module)
    clc_aa_policy.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
