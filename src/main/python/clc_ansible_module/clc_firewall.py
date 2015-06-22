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
#

DOCUMENTATION = '''
module: clc_firewall
short_desciption: Create/delete firewall policies
description:
  - Create or delete firewall polices on Centurylink Centurylink Cloud
options:
  name:
    description:
      - The name of the firewall policy
    default: None
    required: False
    aliases: []
  description:
    description:
      - A description of the firewall policy
    default: None
    required: False
    aliases: []
  location:
    description:
      - Target datacenter for the firewall policy
    default: None
    required: True
    aliases: []
  state:
    description:
      - Whether to create or delete the firewall policy
    default: present
    required: True
    choices: ['present', 'absent']
    aliases: []
  source:
    description:
      - Source addresses for traffic on the originating firewall
    default: None
    required: False
    aliases: []
  destination:
    description:
      - Destination addresses for traffic on the terminating firewall
    default: None
    required: False
    aliases: []
  ports:
    description:
      - types of ports associated with the policy
    default: None
    required: False
    aliases: []
  firewall_policy:
    description:
      - id of the firewall policy
    default: None
    required: False
    aliases: []
  source_account_alias:
    description:
      - CLC alias for the source account
    default: None
    required: True
    aliases: []
  destination_account_alias:
    description:
      - CLC alias for the destination account
    default: None
    required: False
    aliases: []
  wait:
    description:
      - Whether to wait for the provisioning tasks to finish before returning.
    default: True
    required: False
    choices: [ True, False]
    aliases: []


'''

EXAMPLES = '''
'''

import socket
import os

try:
    import clc as clc_sdk
    from clc import CLCException
except ImportError:
    CLC_FOUND = False
    clc_sdk = None
else:
    CLC_FOUND = True

class ClcFirewall():

    clc = None

    STATSD_HOST = '64.94.114.218'
    STATSD_PORT = 2003
    STATS_FIREWALL_CREATE = 'stats_counts.wfaas.clc.ansible.firewall.create'
    STATS_FIREWALL_DELETE = 'stats_counts.wfaas.clc.ansible.firewall.delete'
    SOCKET_CONNECTION_TIMEOUT = 3


    def __init__(self, module):
        """
        Construct module
        """
        self.clc = clc_sdk
        self.module = module
        self.firewall_dict = {}

        if not CLC_FOUND:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            name=dict(required=True),
            location=dict(required=True),
            source_account_alias=dict(default=None),
            destination_account_alias=dict(default=None),
            firewall_policy=dict(default=None),
            wait=dict(default=True),
            state=dict(default='present', choices=['present', 'absent']),
        )
        return argument_spec


    def process_request(self):
        """
        Execute the main code path, and handle the request
        :return: none
        """
        location = self.module.params.get('location')
        group_name = self.module.params.get('name')
        parent_name = self.module.params.get('parent')
        group_description = self.module.params.get('description')
        state = self.module.params.get('state')

        self._set_clc_credentials_from_env()
        self.group_dict = self._get_group_tree_for_datacenter_get_group_tree_for_datacenter(
            datacenter=location)

        if state == "absent":
            changed, group, response = self._ensure_firewall_policy_is_absent()

        else:
            changed, group, response = self._ensure_firewall_policy_is_present()


        self.module.exit_json(changed=changed, group=group_name)

        #
        #  Functions to define the Ansible module and its arguments
        #
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


    def _create_firewall_policy(self, source_account_alias, datacenter, destination_account_alias=None, destinatiion=None, source=None, ports=None ):
        response = self.clc.v2.API.Call('POST', '/v2/sharedLoadBalancers/%s/%s' % (source_account_alias, datacenter))
        ClcFirewall._push_metric(ClcFirewall.STATS_FIREWALL_CREATE, 1)
        return response

    def _delete_firewall_policy(self, source_account_alias, datacenter, firewall_policy):
        response = self.clc.v2.API.Call('POST', '/v2/sharedLoadBalancers/%s/%s/%s' % (source_account_alias, datacenter, firewall_policy))
        ClcFirewall._push_metric(ClcFirewall.STATS_FIREWALL_DELETE, 1)
        return response

    def _ensure_firewall_policy_is_present(self):
        changed = False

    def _ensure_firewall_policy_is_absent(self):
        changed = False

    def _get_firewall_policy(self, source_account_alias, datacenter, firewall_policy):
        response = self.clc.v2.API.Call('GET', '/v2-exerpimental/firewallPolicies/%s/%s/%s' % (source_account_alias, datacenter, firewall_policy))
        return response

    def _get_firewall_policy_list(self, source_account_alias, datacenter, destination_account_alias):
        response = self.clc.v2.API.Call('GET', '/v2-exerpimental/firewallPolicies/%s/%s?destinationAccount=%s' % (source_account_alias, datacenter, destination_account_alias))
        return response

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
            sock.settimeout(ClcFirewall.SOCKET_CONNECTION_TIMEOUT)
            sock.connect((ClcFirewall.STATSD_HOST, ClcFirewall.STATSD_PORT))
            sock.sendall('%s %s %d\n' % (path, count, int(time.time())))
            sock.close()
        except socket.gaierror:
            # do nothing, ignore and move forward
            error = ''
        except socket.error:
            # nothing, ignore and move forward
            error = ''

def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(argument_spec=ClcFirewall._define_module_argument_spec(), supports_check_mode=True)

    clc_firewall = ClcFirewall(module)
    clc_firewall.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
