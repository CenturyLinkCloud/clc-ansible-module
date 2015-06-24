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
short_desciption: Create/delete/update firewall policies
description:
  - Create or delete or updated firewall polices on Centurylink Centurylink Cloud
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
    required: For Creation
    aliases: []
  destination:
    description:
      - Destination addresses for traffic on the terminating firewall
    default: None
    required: For Creation
    aliases: []
  ports:
    description:
      - types of ports associated with the policy. TCP & UDP can take in single ports or port ranges.
    default: None
    required: False
    choices: ['any', 'icmp', 'TCP/123', 'UDP/123', 'TCP/123-456', 'UDP/123-456']
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
    choices: [ True, False ]
    aliases: []
  enabled:
    description:
      - If the firewall policy is enabled or disabled
    default: true
    required: False
    choices: [ true, false ]
    aliases: []

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
        name: 'Test Firewall'
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
        name: 'Test Firewall'
        source_account_alias: WFAD
        location: VA1
        state: present
        firewall_policy: c62105233d7a4231bd2e91b9c791eaae
'''

import socket
import os
import urlparse
import os.path

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
            name=dict(default=None),
            location=dict(required=True, defualt=None),
            source_account_alias=dict(required=True, default=None),
            destination_account_alias=dict(default=None),
            firewall_policy=dict(default=None),
            ports=dict(default=None),
            source=dict(defualt=None),
            destination=dict(defualt=None),
            wait=dict(default=True),
            state=dict(default='present', choices=['present', 'absent']),
            enabled=dict(defualt=None)
        )
        return argument_spec

    def process_request(self):
        """
        Execute the main code path, and handle the request
        :return: none
        """
        name = self.module.params.get('name')
        location = self.module.params.get('location')
        source_account_alias = self.module.params.get('source_account_alias')
        destination_account_alias = self.module.params.get(
            'destination_account_alias')
        firewall_policy = self.module.params.get('firewall_policy')
        ports = self.module.params.get('ports')
        source = self.module.params.get('source')
        destination = self.module.params.get('destination')
        wait = self.module.params.get('wait')
        state = self.module.params.get('state')
        enabled = self.module.params.get('enabled')

        self.firewall_dict = {
            'name': name,
            'location': location,
            'source_account_alias': source_account_alias,
            'destination_account_alias': destination_account_alias,
            'firewall_policy': firewall_policy,
            'ports': ports,
            'source': source,
            'destination': destination,
            'wait': wait,
            'state': state,
            'enabled': enabled}

        self._set_clc_credentials_from_env()

        if state == "absent":
            changed, firewall_policy_id, response = self._ensure_firewall_policy_is_absent(
                source_account_alias, location, self.firewall_dict)

        elif state == "present":
            changed, firewall_policy_id, response = self._ensure_firewall_policy_is_present(
                source_account_alias, location, self.firewall_dict)
        else:
            return self.module.fail_json(msg="Unknown State: " + state)

        # if not self.module.check_mode:
        #     self._wait_for_requests_to_complete(response)

        return self.module.exit_json(
            changed=changed,
            firewall_policy=firewall_policy_id)

    def _wait_for_requests_to_complete(self, requests_lst):
        """
        Waits until the CLC requests are complete if the wait argument is True
        :param requests_lst: The list of CLC request objects
        :return: none
        """
        if self.module.params['wait']:
            for request in requests_lst:
                request.WaitUntilComplete()
                for request_details in request.requests:
                    if request_details.Status() != 'succeeded':
                        self.module.fail_json(
                            msg='Unable to process package install request')

    def _get_policy_id_from_response(self, response):
        url = response.get('links')[0]['href']
        path = urlparse.urlparse(url).path
        path_list = os.path.split(path)
        policy_id = path_list[-1]
        return policy_id

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

    def _create_firewall_policy(
            self,
            source_account_alias,
            location,
            firewall_dict):
        """
        Ensures that a given firewall policy is present
        :param source_account_alias: the source account alias for the firewall policy
        :param location: datacenter of the firewall policy
        :param firewall_dict: dictionary or request parameters for firewall policy creation
        :return: response from CLC API call
        """
        payload = {
            'destinationAccount': firewall_dict.get('destination_account_alias'),
            'source': firewall_dict.get('source'),
            'destination': firewall_dict.get('destination'),
            'ports': firewall_dict.get('ports')}
        try:
            response = self.clc.v2.API.Call(
                'POST', '/v2-experimental/firewallPolicies/%s/%s' %
                (source_account_alias, location), payload)
            ClcFirewall._push_metric(ClcFirewall.STATS_FIREWALL_CREATE, 1)
        except:
            return self.module.fail_json(
                msg="Failed to properly create new firewall policy in %s account in the %s datacenter" %
                (source_account_alias, location))
        return response

    def _delete_firewall_policy(
            self,
            source_account_alias,
            location,
            firewall_policy):
        """
        Deletes a given firewall policy for an account alias in a datacenter
        :param source_account_alias: the source account alias for the firewall policy
        :param location: datacenter of the firewall policy
        :param firewall_policy: firewall policy to delete
        :return: response from CLC API call
        """
        try:
            response = self.clc.v2.API.Call(
                'DELETE', '/v2-experimental/firewallPolicies/%s/%s/%s' %
                (source_account_alias, location, firewall_policy))
            ClcFirewall._push_metric(ClcFirewall.STATS_FIREWALL_DELETE, 1)
        except:
            return self.module.fail_json(
                msg="Failed to properly delete firewall policy %s in account alias %s in the %s datacenter" %
                (firewall_policy, source_account_alias, location))
        return response

    def _ensure_firewall_policy_is_present(
            self,
            source_account_alias,
            location,
            firewall_dict):
        """
        Ensures that a given firewall policy is present
        :param source_account_alias: the source account alias for the firewall policy
        :param location: datacenter of the firewall policy
        :param firewall_dict: dictionary or request parameters for firewall policy creation
        :return: (changed, firewall_policy, response)
            changed: flag for if a change occurred
            firewall_policy: policy that was changed
            response: response from CLC API call
        """
        changed = False
        response = []
        firewall_policy_id = None
        if not self.module.check_mode:
            try:
                response = self.clc.v2.API.Call(
                    'PUT',
                    '/v2-experimental/firewallPolicies/%s/%s/%s' %
                    (source_account_alias,
                     location,
                     firewall_dict.get('firewall_policy')),
                    firewall_dict)
                firewall_policy_id = firewall_dict.get('firewall_policy')
            except:
                response = self._create_firewall_policy(
                    source_account_alias,
                    location,
                    firewall_dict)
                firewall_policy_id = self._get_policy_id_from_response(
                    response)
        changed = True
        return changed, firewall_policy_id, response

    def _ensure_firewall_policy_is_absent(
            self,
            source_account_alias,
            location,
            firewall_dict):
        """
        Ensures that a given firewall policy is removed if present
        :param source_account_alias: the source account alias for the firewall policy
        :param location: datacenter of the firewall policy
        :param firewall_policy: firewall policy to delete
        :return: (changed, firewall_policy, response)
            changed: flag for if a change occurred
            firewall_policy: policy that was changed
            response: response from CLC API call
        """
        changed = False
        response = []
        firewall_policy = firewall_dict.get('firewall_policy')
        result, success = self._get_firewall_policy(
            source_account_alias, location, firewall_policy)
        if success:
            if not self.module.check_mode:
                response = self._delete_firewall_policy(
                    source_account_alias,
                    location,
                    firewall_policy)
            changed = True
        return changed, firewall_policy, response

    def _get_firewall_policy(
            self,
            source_account_alias,
            location,
            firewall_policy):
        """
        Get back details for a particular firewall policy
        :param source_account_alias: the source account alias for the firewall policy
        :param location: datacenter of the firewall policy
        :param firewall_policy: id of the firewall policy to get
        :return: response from CLC API call
        """
        response = []
        success = False
        try:
            response = self.clc.v2.API.Call(
                'GET', '/v2-experimental/firewallPolicies/%s/%s/%s' %
                (source_account_alias, location, firewall_policy))
            success = True
        except:
            pass
        return response, success

    def _get_firewall_policy_list(
            self,
            source_account_alias,
            location,
            destination_account_alias=None):
        """
        Get back a list of firewall policies from a certain datacenter
        :param source_account_alias: the source account alias for the firewall policy
        :param location: datacenter of the firewall policy
        :param destination_account_alias: the destination account alias for the firewall policy
        :return: response from CLC API call
        """
        try:
            if destination_account_alias is None:
                response = self.clc.v2.API.Call(
                    'GET', '/v2-experimental/firewallPolicies/%s/%s' %
                    (source_account_alias, location))
            else:
                response = self.clc.v2.API.Call(
                    'GET', '/v2-experimental/firewallPolicies/%s/%s?destinationAccount=%s' %
                    (source_account_alias, location, destination_account_alias))
        except:
            return self.module.fail_json(
                msg="Failed to get polices from the %s datacenter" %
                location)
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
    module = AnsibleModule(
        argument_spec=ClcFirewall._define_module_argument_spec(),
        supports_check_mode=True)

    clc_firewall = ClcFirewall(module)
    clc_firewall.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
