#!/usr/bin/python
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
        self.module = module
        self.policy_dict = {}
        self.clc = clc_sdk

    # Ansible module goodness

    @staticmethod
    def _define_argument_spec():
        argument_spec = dict(
            name=dict(required=True),
            location=dict(required=True),
            alias=dict(default=None),
            wait=dict(type='bool', default=False),
            state=dict(default='present', choices=['present', 'absent']),
            )
        return argument_spec

    # Module Behavior Goodness
    def do_work(self):
        p = self.module.params

        if not clc_found:
            self.module.fail_json(msg='clc-python-sdk required for this module')

        self._clc_set_credentials()
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

    def _clc_set_credentials(self):
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
        response = {}

        policies = self.clc.v2.AntiAffinity.GetAll(location=p['location'])
        
        for policy in policies:
            response[policy.name] = policy
        return response

    def _create_policy(self, p):
        ClcAntiAffinityPolicy._push_metric(ClcAntiAffinityPolicy.STATS_AAPOLICY_CREATE, 1)
        return self.clc.v2.AntiAffinity.Create(name=p['name'], location=p['location'])

    def _delete_policy(self, p):
        policy = self.policy_dict[p['name']]
        policy.Delete()
        ClcAntiAffinityPolicy._push_metric(ClcAntiAffinityPolicy.STATS_AAPOLICY_DELETE, 1)

    def _policy_exists(self, policy_name):
        if policy_name in self.policy_dict:
            return True

        return False

    def _ensure_policy_is_absent(self, p):
        changed = False
        policy = None

        if self._policy_exists(policy_name=p['name']):
            self._delete_policy(p)
            changed = True
        return changed, policy

    def _ensure_policy_is_present(self, p):
        changed = False
        policy = None

        if not self._policy_exists(policy_name=p['name']):
            policy = self._create_policy(p)
            changed = True

        return changed, policy

    @staticmethod
    def _push_metric(path, count):
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
    module = AnsibleModule(argument_spec=ClcAntiAffinityPolicy.define_argument_spec()   )
    me = ClcAntiAffinityPolicy(module)
    me.do_work()

if __name__ == '__main__':
    main()
