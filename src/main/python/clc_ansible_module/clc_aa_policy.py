#!/usr/bin/python

# CenturyLink Cloud Ansible Modules.
#
# These Ansible modules enable the CenturyLink Cloud v2 API to be called
# from an within Ansible Playbook.
#
# This file is part of CenturyLink Cloud, and is maintained
# by the Workflow as a Service Team
#
# Copyright 2015 CenturyLink Cloud
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
short_descirption: Create or Deletes Anti Affinity Policies at CenturyLink Cloud.
description:
  - An Ansible module to Create or Deletes Anti Affinity Policies at CenturyLink Cloud.
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
      - Whether to wait for the provisioning tasks to finish before returning.
    default: True
    required: False
    choices: [ True, False]
    aliases: []
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

import sys
import os
import datetime
import json
import socket
import time
from ansible.module_utils.basic import *

#
#  Requires the clc-python-sdk.
#  sudo pip install clc-sdk
#
try:
    import clc as clc_sdk
    from clc import CLCException
except ImportError:
    clc_found = False
    clc_sdk = None
else:
    clc_found = True

class ClcAntiAffinityPolicy():

    STATSD_HOST = '64.94.114.218'
    STATSD_PORT = 2003
    STATS_AAPOLICY_CREATE = 'stats_counts.wfaas.clc.ansible.aapolicy.create'
    STATS_AAPOLICY_DELETE = 'stats_counts.wfaas.clc.ansible.aapolicy.delete'
    SOCKET_CONNECTION_TIMEOUT = 3

    def __init__(self, module):
        """
        Construct module
        """
        self.module = module
        self.policy_dict = {}
        self.clc = clc_sdk

    # Ansible module goodness

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            name=dict(required=True),
            location=dict(required=True),
            alias=dict(default=None),
            wait=dict(type='bool', default=False),
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

        if not clc_found:
            self.module.fail_json(msg='clc-python-sdk required for this module')

        self._set_clc_credentials_from_env()
        self.policy_dict = self._get_policies_for_datacenter(p)
        
        if p['state'] == "absent":
            changed, policy = self._ensure_policy_is_absent(p)
        else:
            changed, policy = self._ensure_policy_is_present(p)

        if hasattr(policy, 'data'):
            policy = policy.data
        elif hasattr(policy, '__dict__'):
            policy = policy.__dict__

        self.module.exit_json(changed=changed, policy=policy)

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

    def _get_policies_for_datacenter(self, p):
        """
        Get the Policies for a datacenter by calling the CLC API.
        :param p: datacenter to get policies from
        :return: policies in the datacenter
        """
        response = {}

        if not self.module.check_mode:
            policies = self.clc.v2.AntiAffinity.GetAll(location=p['location'])
        
        for policy in policies:
            response[policy.name] = policy
        return response

    def _create_policy(self, p):
        """
        Create an Anti Affinnity Policy using the CLC API.
        :param p: datacenter to create policy in
        :return: response dictionary from the CLC API.
        """
        if not self.module.check_mode:
            ClcAntiAffinityPolicy._push_metric(ClcAntiAffinityPolicy.STATS_AAPOLICY_CREATE, 1)
        return self.clc.v2.AntiAffinity.Create(name=p['name'], location=p['location'])

    def _delete_policy(self, p):
        """
        Delete an Anti Affinity Policy using the CLC API.
        :param p: datacenter to delete a policy from
        :return: none
        """
        policy = self.policy_dict[p['name']]
        policy.Delete()
        if not self.module.check_mode:
            ClcAntiAffinityPolicy._push_metric(ClcAntiAffinityPolicy.STATS_AAPOLICY_DELETE, 1)

    def _policy_exists(self, policy_name):
        """
        Check to see if an Anti Affinity Policy exists
        :param policy_name: name of the policy
        :return: boolean of if the policy exists
        """
        if policy_name in self.policy_dict:
            return True

        return False

    def _ensure_policy_is_absent(self, p):
        """
        Makes sure that a policy is absent
        :param p: dictionary of policy name
        :return: tuple of if a deletion occurred and the name of the policy that was deleted
        """
        changed = False
        policy = None

        if self._policy_exists(policy_name=p['name']):
            self._delete_policy(p)
            changed = True
        return changed, policy

    def _ensure_policy_is_present(self, p):
        """
        Ensures that a policy is present
        :param p: dictonary of a policy name
        :return: tuple of if an addition occurred and the name of the policy that was added
        """
        changed = False
        policy = None

        if not self._policy_exists(policy_name=p['name']):
            policy = self._create_policy(p)
            changed = True

        return changed, policy

    @staticmethod
    def _push_metric(path, count):
        """
        Sends the usage metric to statsd
        :param path: The metric path
        :param count: The number of ticks to record to the metric
        :return None
        """
        try:
            sock = socket.socket()
            sock.settimeout(ClcAntiAffinityPolicy.SOCKET_CONNECTION_TIMEOUT)
            sock.connect((ClcAntiAffinityPolicy.STATSD_HOST, ClcAntiAffinityPolicy.STATSD_PORT))
            sock.sendall('%s %s %d\n' %(path, count, int(time.time())))
            sock.close()
        except socket.gaierror:
            # do nothing, ignore and move forward
            error = ''
        except socket.error:
            #nothing, ignore and move forward
            error = ''

def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    argument_dict = ClcAntiAffinityPolicy._define_module_argument_spec()
    module = AnsibleModule(supports_check_mode=True, **argument_dict)
    me = ClcAntiAffinityPolicy(module)
    me.do_work()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
