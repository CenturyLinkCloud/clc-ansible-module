#!/usr/bin/python

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
    def define_argument_spec():
        argument_spec = dict(
            name=dict(required=True),
            location=dict(required=True),
            alias=dict(default=None),
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
            e = os.environ

            v2_api_passwd = None
            v2_api_username = None

            try:
                v2_api_username = e['CLC_V2_API_USERNAME']
                v2_api_passwd = e['CLC_V2_API_PASSWD']
            except KeyError, e:
                self.module.fail_json(msg = "you must set the CLC_V2_API_USERNAME and CLC_V2_API_PASSWD environment variables")

            self.clc.v2.SetCredentials(api_username=v2_api_username, api_passwd=v2_api_passwd)

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
