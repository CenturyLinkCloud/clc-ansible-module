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
module: clc_modify_server
short_description: modify servers in CenturyLink Cloud.
description:
  - An Ansible module to modify servers in CenturyLink Cloud.
version_added: "2.0"
options:
  server_ids:
    description:
      - A list of server Ids to modify.
    required: True
  cpu:
    description:
      - How many CPUs to update on the server
    required: False
    default: None
  memory:
    description:
      - Memory (in GB) to set to the server.
    required: False
    default: None
  anti_affinity_policy_id:
    description:
      - The anti affinity policy id to be set for a hyper scale server.
        This is mutually exclusive with 'anti_affinity_policy_name'
    required: False
    default: None
  anti_affinity_policy_name:
    description:
      - The anti affinity policy name to be set for a hyper scale server.
        This is mutually exclusive with 'anti_affinity_policy_id'
    required: False
    default: None
  alert_policy_id:
    description:
      - The alert policy id to be associated to the server.
        This is mutually exclusive with 'alert_policy_name'
    required: False
    default: None
  alert_policy_name:
    description:
      - The alert policy name to be associated to the server.
        This is mutually exclusive with 'alert_policy_id'
    required: False
    default: None
  additional_network:
    description:
      - The additional network id/name that needs to be added to the server
    required: False
    default: None
  state:
    description:
      - The state to insure that the provided resources are in.
    default: 'present'
    required: False
    choices: ['present', 'absent']
  wait:
    description:
      - Whether to wait for the provisioning tasks to finish before returning.
    default: True
    required: False
    choices: [ True, False]
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

- name: set the cpu count to 4 on a server
  clc_modify_server:
    server_ids:
        - UC1TESTSVR01
        - UC1TESTSVR02
    cpu: 4
    state: present

- name: set the memory to 8GB on a server
  clc_modify_server:
    server_ids:
        - UC1TESTSVR01
        - UC1TESTSVR02
    memory: 8
    state: present

- name: add a secondary nic
  clc_modify_server:
    server_ids:
        - UC1TESTSVR01
        - UC1TESTSVR02
    additional_network: 613a25aff2124d10a71b16cd6fb28975
    state: present

- name: remove a secondary nic
  clc_modify_server:
    server_ids:
        - UC1TESTSVR01
        - UC1TESTSVR02
    additional_network: '10.11.12.0/24'
    state: absent

- name: set the anti affinity policy on a server
  clc_modify_server:
    server_ids:
        - UC1TESTSVR01
        - UC1TESTSVR02
    anti_affinity_policy_name: 'aa_policy'
    state: present

- name: remove the anti affinity policy on a server
  clc_modify_server:
    server_ids:
        - UC1TESTSVR01
        - UC1TESTSVR02
    anti_affinity_policy_name: 'aa_policy'
    state: absent

- name: add the alert policy on a server
  clc_modify_server:
    server_ids:
        - UC1TESTSVR01
        - UC1TESTSVR02
    alert_policy_name: 'alert_policy'
    state: present

- name: remove the alert policy on a server
  clc_modify_server:
    server_ids:
        - UC1TESTSVR01
        - UC1TESTSVR02
    alert_policy_name: 'alert_policy'
    state: absent

- name: set the memory to 16GB and cpu to 8 core on a lust if servers
  clc_modify_server:
    server_ids:
        - UC1TESTSVR01
        - UC1TESTSVR02
    cpu: 8
    memory: 16
    state: present
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
            "UC1TEST-SVR01",
            "UC1TEST-SVR02"
        ]
servers:
    description: The list of server objects that are changed
    returned: success
    type: list
    sample:
        [
           {
              "changeInfo":{
                 "createdBy":"service.wfad",
                 "createdDate":1438196820,
                 "modifiedBy":"service.wfad",
                 "modifiedDate":1438196820
              },
              "description":"test-server",
              "details":{
                 "alertPolicies":[

                 ],
                 "cpu":1,
                 "customFields":[

                 ],
                 "diskCount":3,
                 "disks":[
                    {
                       "id":"0:0",
                       "partitionPaths":[

                       ],
                       "sizeGB":1
                    },
                    {
                       "id":"0:1",
                       "partitionPaths":[

                       ],
                       "sizeGB":2
                    },
                    {
                       "id":"0:2",
                       "partitionPaths":[

                       ],
                       "sizeGB":14
                    }
                 ],
                 "hostName":"",
                 "inMaintenanceMode":false,
                 "ipAddresses":[
                    {
                       "internal":"10.1.1.1"
                    }
                 ],
                 "memoryGB":1,
                 "memoryMB":1024,
                 "partitions":[

                 ],
                 "powerState":"started",
                 "snapshots":[

                 ],
                 "storageGB":17
              },
              "groupId":"086ac1dfe0b6411989e8d1b77c4065f0",
              "id":"test-server",
              "ipaddress":"10.120.45.23",
              "isTemplate":false,
              "links":[
                 {
                    "href":"/v2/servers/wfad/test-server",
                    "id":"test-server",
                    "rel":"self",
                    "verbs":[
                       "GET",
                       "PATCH",
                       "DELETE"
                    ]
                 },
                 {
                    "href":"/v2/groups/wfad/086ac1dfe0b6411989e8d1b77c4065f0",
                    "id":"086ac1dfe0b6411989e8d1b77c4065f0",
                    "rel":"group"
                 },
                 {
                    "href":"/v2/accounts/wfad",
                    "id":"wfad",
                    "rel":"account"
                 },
                 {
                    "href":"/v2/billing/wfad/serverPricing/test-server",
                    "rel":"billing"
                 },
                 {
                    "href":"/v2/servers/wfad/test-server/publicIPAddresses",
                    "rel":"publicIPAddresses",
                    "verbs":[
                       "POST"
                    ]
                 },
                 {
                    "href":"/v2/servers/wfad/test-server/credentials",
                    "rel":"credentials"
                 },
                 {
                    "href":"/v2/servers/wfad/test-server/statistics",
                    "rel":"statistics"
                 },
                 {
                    "href":"/v2/servers/wfad/510ec21ae82d4dc89d28479753bf736a/upcomingScheduledActivities",
                    "rel":"upcomingScheduledActivities"
                 },
                 {
                    "href":"/v2/servers/wfad/510ec21ae82d4dc89d28479753bf736a/scheduledActivities",
                    "rel":"scheduledActivities",
                    "verbs":[
                       "GET",
                       "POST"
                    ]
                 },
                 {
                    "href":"/v2/servers/wfad/test-server/capabilities",
                    "rel":"capabilities"
                 },
                 {
                    "href":"/v2/servers/wfad/test-server/alertPolicies",
                    "rel":"alertPolicyMappings",
                    "verbs":[
                       "POST"
                    ]
                 },
                 {
                    "href":"/v2/servers/wfad/test-server/antiAffinityPolicy",
                    "rel":"antiAffinityPolicyMapping",
                    "verbs":[
                       "PUT",
                       "DELETE"
                    ]
                 },
                 {
                    "href":"/v2/servers/wfad/test-server/cpuAutoscalePolicy",
                    "rel":"cpuAutoscalePolicyMapping",
                    "verbs":[
                       "PUT",
                       "DELETE"
                    ]
                 }
              ],
              "locationId":"UC1",
              "name":"test-server",
              "os":"ubuntu14_64Bit",
              "osType":"Ubuntu 14 64-bit",
              "status":"active",
              "storageType":"standard",
              "type":"standard"
           }
        ]
'''

__version__ = '${version}'

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException


class ClcModifyServer(object):

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
        cpu = int(p.get('cpu')) if p.get('cpu') else None
        memory = int(p.get('memory')) if p.get('memory') else None
        state = p.get('state')
        if state == 'absent' and (cpu or memory):
            return self.module.fail_json(
                msg='\'absent\' state is not supported for \'cpu\' and \'memory\' arguments')

        server_ids = p['server_ids']

        (changed, server_dict_array, changed_server_ids) = self._modify_servers(
            server_ids=server_ids)

        self.module.exit_json(
            changed=changed,
            server_ids=changed_server_ids,
            servers=server_dict_array)

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            server_ids=dict(type='list', required=True),
            state=dict(type='str', default='present',
                       choices=['present', 'absent']),
            location=dict(type='str', default=None),
            cpu=dict(type='int', default=None),
            memory=dict(type='int', default=None),
            anti_affinity_policy_id=dict(type='str', default=None),
            anti_affinity_policy_name=dict(type='str', default=None),
            alert_policy_id=dict(type='str', default=None),
            alert_policy_name=dict(type='str', default=None),
            wait=dict(type='bool', default=True),
            additional_network=dict(type='str', default=None),
        )
        mutually_exclusive = [
            ['anti_affinity_policy_id', 'anti_affinity_policy_name'],
            ['alert_policy_id', 'alert_policy_name']
        ]
        return {"argument_spec": argument_spec,
                "mutually_exclusive": mutually_exclusive}

    def _modify_servers(self, server_ids):
        """
        modify the servers configuration on the provided list
        :param server_ids: list of servers to modify
        :return: a list of dictionaries with server information about the servers that were modified
        """
        p = self.module.params
        state = p.get('state')
        changed = False
        server_changed = False
        aa_changed = False
        ap_changed = False
        nic_changed = False
        server_dict_array = []
        result_server_ids = []
        request_list = []
        changed_servers = []

        if len(server_ids) < 1:
            return self.module.fail_json(
                msg='server_ids should be a list of servers, aborting')

        servers = clc_common.servers_by_id(self.module, self.clc_auth,
                                           server_ids)
        for server in servers:
            if state == 'present':
                server_changed, server_result = self._ensure_server_config(
                    server)
                if server_result:
                    request_list.append(server_result)
                aa_changed = self._ensure_aa_policy_present(server)
                ap_changed = self._ensure_alert_policy_present(server)
                nic_changed = self._ensure_nic_present(server)
            elif state == 'absent':
                aa_changed = self._ensure_aa_policy_absent(server)
                ap_changed = self._ensure_alert_policy_absent(server)
                nic_changed = self._ensure_nic_absent(server)
            if server_changed or aa_changed or ap_changed or nic_changed:
                changed_servers.append(server)
                changed = True

        self._wait_for_requests(request_list)
        changed_servers = self._refresh_servers(changed_servers)

        for server in changed_servers:
            server_dict_array.append(server.data)
            result_server_ids.append(server.id)

        return changed, server_dict_array, result_server_ids

    def _ensure_server_config(self, server):
        """
        ensures the server is updated with the provided cpu and memory
        :param server: the CLC server object
        :return: (changed, group) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        cpu = self.module.params.get('cpu')
        memory = self.module.params.get('memory')
        changed = False
        result = None

        if not cpu:
            cpu = server.data['details']['cpu']
        if not memory:
            memory = server.data['details']['memoryGB']
        if (memory != server.data['details']['memoryGB']
                or cpu != server.data['details']['cpu']):
            if not self.module.check_mode:
                result = self._modify_clc_server(server.id, cpu, memory)
            changed = True
        return changed, result

    def _modify_clc_server(self, server_id, cpu, memory):
        """
        Modify the memory or CPU of a clc server.
        :param server_id: id of the server to modify
        :param cpu: the new cpu value
        :param memory: the new memory value
        :return: the result of CLC API call
        """
        result = None
        try:
            result = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'PATCH', '/servers/{alias}/{id}'.format(
                    alias=self.clc_auth['clc_alias'], id=server_id),
                data=[
                    {'op': 'set', 'member': 'memory', 'value': memory},
                    {'op': 'set', 'member': 'cpu', 'value': cpu}
                ]
            )
        except ClcApiException as ex:
            return self.module.fail_json(
                msg='Unable to update the server configuration for '
                    'server: {id}. {msg}'.format(
                        id=server_id, msg=ex.message))
        return result

    def _modify_add_nic(self, server_id):
        """
        Add a secondary nic to existing clc server
        :param server_id: id of the server to modify
        :return:
        """
        result = None
        dc = self._find_datacenter()
        network_id = self._find_network_id(dc)
        if not self.module.check_mode:
            try:
                response = clc_common.call_clc_api(
                    self.module, self.clc_auth,
                    'POST',
                    '/servers/{alias}/{server}/networks'.format(
                        alias=self.clc_auth['clc_alias'], server=server_id),
                    data={'networkId': network_id})
                self._wait_for_requests([response])
                result = True
            except ClcApiException as ex:
                if 'already has an adapter' in ex.message:
                    result = False
                else:
                    return self.module.fail_json(
                        msg='Unable to add NIC to server: {id}. {msg}'.format(
                            id=server_id, msg=ex.message))
        return result

    def _modify_remove_nic(self, server_id):
        """
        Remove a secondary nic to existing clc server
        :param server_id: id of the server to modify
        :return:
        """
        result = None
        dc = self._find_datacenter()
        network_id = self._find_network_id(dc)
        if not self.module.check_mode:
            try:
                response = clc_common.call_clc_api(
                    self.module, self.clc_auth,
                    'DELETE',
                    '/servers/{alias}/{server}/networks/{network}'.format(
                        alias=self.clc_auth['clc_alias'], server=server_id,
                        network=network_id))
                self._wait_for_requests([response])
                result = True
            except ClcApiException as ex:
                if 'has no secondary adapter' in ex.message:
                    result = False
                else:
                    return self.module.fail_json(
                        msg='Unable to remove NIC from server: {id}. '
                            '{msg}'.format(id=server_id, msg=ex.message))
        return result

    def _find_datacenter(self):
        """
        Find or Validate the datacenter by calling the CLC API.
        :return: Datacenter ID
        """
        location = self.module.params.get('location')
        try:
            if 'clc_location' not in self.clc_auth:
                self.clc_auth = clc_common.authenticate(self.module)
            if not location:
                location = self.clc_auth['clc_location']
            else:
                # Override authentication with user-provided location
                self.clc_auth['clc_location'] = location
            return location
        except ClcApiException as ex:
            self.module.fail_json(
                msg=str(
                    "Unable to find location: {location}".format(
                        location=location)))

    def _find_network_id(self, datacenter):
        """
        Validate the provided network id or return a default.
        :param datacenter: the datacenter to search for a network id
        :return: a valid network id
        """
        network_id_search = self.module.params.get('additional_network')

        network = clc_common.find_network(
            self.module, self.clc_auth, datacenter, network_id_search)
        if network is None:
            return self.module.fail_json(
                msg='No matching network: {network} '
                    'found in location: {location}'.format(
                        network=network_id_search, location=datacenter))
        return network.id

    def _ensure_nic_present(self, server):
        """
        :param server: server to add nic
        :return:
        """
        changed = False
        additional_network = self.module.params.get('additional_network')
        if additional_network:
            if not self.module.check_mode:
                add_nic = self._modify_add_nic(server.id)
                changed = add_nic
        return changed

    def _ensure_nic_absent(self, server):
        """
        :param server: server from which to remove nic
        :return: True or False
        """
        changed = False
        additional_network = self.module.params.get('additional_network')
        if additional_network:
            if not self.module.check_mode:
                changed = self._modify_remove_nic(server.id)
        return changed

    def _wait_for_requests(self, request_list):
        """
        Block until server provisioning requests are completed.
        :param request_list: a list of CLC API JSON responses
        :return: none
        """
        wait = self.module.params.get('wait')
        if wait:
            failed_requests_count = clc_common.wait_on_completed_operations(
                self.module, self.clc_auth,
                clc_common.operation_id_list(request_list))

            if failed_requests_count > 0:
                self.module.fail_json(
                    msg='Unable to process modify server request')

    def _refresh_servers(self, servers, poll_freq=2):
        """
        Loop through a list of servers and refresh them.
        :param servers: list of Server objects to refresh
        :return: none
        """
        server_ids = [s.id for s in servers]
        try:
            refreshed_servers = clc_common.servers_by_id(
                self.module, self.clc_auth, server_ids)
        except ClcApiException as ex:
            return self.module.fail_json(
                msg='Unable to refresh servers. {msg}'.format(
                    msg=ex.message))
        return refreshed_servers

    def _ensure_aa_policy_present(self, server):
        """
        ensures the server is updated with the provided anti affinity policy
        :param server: the CLC server object
        :return: (changed, group) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        changed = False
        aa_policy_id = self.module.params.get('anti_affinity_policy_id')
        aa_policy_name = self.module.params.get('anti_affinity_policy_name')
        search_key = (aa_policy_id or aa_policy_name)
        if search_key is None:
            return changed
        aa_policy = clc_common.find_policy(
            self.module, self.clc_auth, search_key, policy_type='antiAffinity')
        if aa_policy is None:
            return self.module.fail_json(
                msg='No anti affinity policy matching: {search}.'.format(
                    search=search_key))
        if not self._aa_policy_exists_on_server(server.id, aa_policy['id']):
            if not self.module.check_mode:
                clc_common.modify_aa_policy_on_server(
                    self.module, self.clc_auth, server.id, aa_policy['id'])
            changed = True
        return changed

    def _ensure_aa_policy_absent(self, server):
        """
        ensures the the provided anti affinity policy is removed from the server
        :param server: the CLC server object
        :return: (changed, group) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        changed = False
        aa_policy_id = self.module.params.get('anti_affinity_policy_id')
        aa_policy_name = self.module.params.get('anti_affinity_policy_name')
        search_key = (aa_policy_id or aa_policy_name)
        if search_key is None:
            return changed
        aa_policy = clc_common.find_policy(
            self.module, self.clc_auth, search_key, policy_type='antiAffinity')
        if aa_policy is None:
            return self.module.fail_json(
                msg='No anti affinity policy matching: {search}.'.format(
                    search=search_key))
        if self._aa_policy_exists_on_server(server.id, aa_policy['id']):
            if not self.module.check_mode:
                clc_common.remove_aa_policy_from_server(
                    self.module, self.clc_auth, server.id, aa_policy['id'])
            changed = True
        return changed

    def _aa_policy_exists_on_server(self, server_id, aa_policy_id):
        """
        retrieves the anti affinity policy id of the server based on the CLC server id
        :param server_id: the CLC server id
        :return: aa_policy_id: The anti affinity policy id
        """
        result = False
        try:
            response = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'GET', '/servers/{alias}/{id}/antiAffinityPolicy'.format(
                    alias=self.clc_auth['clc_alias'], id=server_id))
            if response.get('id') == aa_policy_id:
                result = True
        except ClcApiException as ex:
            if ex.code != 404:
                self.module.fail_json(
                    msg='Unable to fetch anti affinity policy for '
                        'server: {id}. {msg}'.format(
                            id=server_id, msg=ex.message))
        return result

    def _ensure_alert_policy_present(self, server):
        """
        ensures the server is updated with the provided alert policy
        :param server: the CLC server object
        :return: (changed, group) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        changed = False
        alert_policy_id = self.module.params.get('alert_policy_id')
        alert_policy_name = self.module.params.get('alert_policy_name')
        search_key = (alert_policy_id or alert_policy_name)
        if search_key is None:
            return changed
        alert_policy = clc_common.find_policy(self.module, self.clc_auth,
                                              search_key, policy_type='alert')
        if alert_policy is None:
            return self.module.fail_json(
                msg='No alert policy matching: {search}.'.format(
                    search=search_key))
        if not self._alert_policy_exists_on_server(server, alert_policy['id']):
            if not self.module.check_mode:
                clc_common.add_alert_policy_to_server(
                    self.module, self.clc_auth, server.id, alert_policy['id'])
            changed = True
        return changed

    def _ensure_alert_policy_absent(self, server):
        """
        ensures the alert policy is removed from the server
        :param server: the CLC server object
        :return: (changed, group) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        changed = False
        alert_policy_id = self.module.params.get('alert_policy_id')
        alert_policy_name = self.module.params.get('alert_policy_name')
        search_key = (alert_policy_id or alert_policy_name)
        if search_key is None:
            return changed
        alert_policy = clc_common.find_policy(self.module, self.clc_auth,
                                              search_key, policy_type='alert')
        if alert_policy is None:
            return self.module.fail_json(
                msg='No alert policy matching: {search}.'.format(
                    search=search_key))
        if self._alert_policy_exists_on_server(server, alert_policy['id']):
            if not self.module.check_mode:
                clc_common.remove_alert_policy_from_server(
                    self.module, self.clc_auth, server.id, alert_policy['id'])
            changed = True
        return changed

    @staticmethod
    def _alert_policy_exists_on_server(server, alert_policy_id):
        """
        Checks if the alert policy exists for the server
        :param server: the clc server object
        :param alert_policy_id: the alert policy
        :return: True: if the given alert policy id associated to the server, False otherwise
        """
        result = False
        alert_policies = server.data['details']['alertPolicies']
        if alert_policies:
            for alert_policy in alert_policies:
                if alert_policy.get('id') == alert_policy_id:
                    result = True
        return result


def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """

    argument_dict = ClcModifyServer._define_module_argument_spec()
    module = AnsibleModule(supports_check_mode=True, **argument_dict)
    clc_modify_server = ClcModifyServer(module)
    clc_modify_server.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
