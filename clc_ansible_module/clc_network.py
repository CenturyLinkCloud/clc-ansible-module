#!/usr/bin/env python
# -*- coding: utf-8 -*-

# CenturyLink Cloud Ansible Modules.
#
# These Ansible modules enable the CenturyLink Cloud v2 API to be called
# from an within Ansible Playbook.
#
# This file is part of CenturyLink Cloud
#
# Copyright 2016 CenturyLink
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
# CenturyLink Cloud: http://www.ctl.op
# API Documentation: https://www.ctl.io/api-docs/v2/

DOCUMENTATION = '''
module: clc_network
short_description: Create or Delete networks at CenturyLink Cloud.
description:
  - An Ansible module to Create or Delete networks at CenturyLink Cloud.
version_added: "2.0"
options:
  description:
    description:
      - A free text field for describing the network's purpose
    required: False
  id:
    description:
      - The id for the network being updated or deleted; required when state = 'absent'.
        This can be the network's id, name, or vlan -- as these can all be used to uniquely id the network.
    required: False
  location:
    description:
      - Datacenter in which the network lives/should live.
    required: True
  name:
    description:
      - The name of the network.  Used to find an existing network when state='present'.
    required: False
  state:
    description:
      - Whether to claim or release the network.
    required: False
    default: present
    choices: ['present','absent']
  wait:
    description:
      - Whether to wait for the tasks to finish before returning.
        This doesn't work when state 'present' with a name as the name is being set after the network being created.
    default: True
    required: False
    choices: [True, False]
requirements:
    - python = 2.7
    - clc-sdk
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
- name: Create Network
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create and update a new network
      clc_network:
        location: 'ut1'
        state: present
        name: 'ProdNet5000'
        description: 'Production Minecraft'
      register: net

    - debug: var=net

---
- name: Delete Network
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Delete a CLC network based on id
      clc_network:
        location: 'ut1'
        state: absent
        id: 'vlan_1306_10.81.206'
      register: net

    - debug: var=net
'''

RETURN = '''
changed:
    description: A flag indicating if any change was made or not
    returned: success
    type: boolean
    sample: True
network:
    description: The network information
    returned: success
    type: dict
    sample:
        {
            "cidr": "10.101.216.0/24",
            "description": "The testing place",
            "gateway": "10.101.216.1",
            "id": "7c5fc52fd9dd48d5a6ab879bf6ab3db9",
            "links": [
                {
                    "href": "/v2-experimental/networks/wftc/ca3/7c5fc52fd9dd48d5a6ab879bf6ab3db9",
                    "rel": "self",
                    "verbs": [
                        "GET",
                        "PUT"
                    ]
                },
                {
                    "href": "/v2-experimental/networks/wftc/ca3/7c5fc52fd9dd48d5a6ab879bf6ab3db9/ipAddresses",
                    "rel": "ipAddresses",
                    "verbs": [
                        "GET"
                    ]
                },
                {
                    "href": "/v2-experimental/networks/wftc/ca3/7c5fc52fd9dd48d5a6ab879bf6ab3db9/release",
                    "rel": "release",
                    "verbs": [
                        "POST"
                    ]
                }
            ],
            "name": "test9001",
            "netmask": "255.255.255.0",
            "type": "private",
            "vlan": 716
        }
'''

__version__ = '${version}'

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException

class ClcNetwork(object):

    module = None

    def __init__(self, module):
        """
        Construct module
        """
        self.clc_auth = {}
        self.module = module
        self.networks = None

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            id=dict(required=False),
            name=dict(required=False),
            location=dict(required=True),
            description=dict(required=False),
            wait=dict(default=True, type='bool'),
            state=dict(default='present', choices=['present', 'absent']),
        )
        return argument_spec

    # Module Behavior Goodness
    def process_request(self):
        """
        Process the request - Main Code Path
        :return: Returns with either an exit_json or fail_json
        """
        network = None
        p = self.module.params

        self.clc_auth = clc_common.authenticate(self.module)
        # Network operations use v2-experimental, so over-ride default
        self.clc_auth['v2_api_url'] = 'https://api.ctl.io/v2-experimental/'

        location = p.get('location')
        if location:
            # Over-ride location in clc_auth
            self.clc_auth['clc_location'] = location
        else:
            location = self.clc_auth['clc_location']
        search_key = p.get('id', None) or p.get('name', None)

        self.networks = clc_common.networks_in_datacenter(
            self.module, self.clc_auth, location)

        if p.get('state') == 'absent':
            changed = self._ensure_network_absent(location, search_key)
        else:
            changed, network = self._ensure_network_present(location,
                                                            search_key)

        if hasattr(network, 'data'):
            network = network.data
        elif isinstance(network, dict) and network.get('operationId'):
            network = {
                "id": network['operationId'],
                "uri": network['uri'],
            }

        self.module.exit_json(changed=changed, network=network)

    # TODO: Complete method docstrings

    def _ensure_network_absent(self, location, search_key):
        """
        Check to make sure network matching 'search_key' does not exist
        :param location: Datacenter in which to search
        :param search_key: Value to search for in networks
        :return: Boolean indicating whether a change took place
        """
        if not search_key:
            return self.module.fail_json(
                msg='Must specify either a network name or id')
        changed = False

        network = clc_common.find_network(self.module, self.clc_auth,
                                          location,
                                          network_id_search=search_key,
                                          networks=self.networks)

        if network is not None:
            if not self.module.check_mode:
                self._delete_network(location, network)
            changed = True

        return changed

    def _ensure_network_present(self, location, search_key):
        """
        Check to make sure network matching 'search_key' exists
        :param location:  Datacenter in which to search
        :param search_key: Value to search for in networks
        :return: Boolean indicating change, and network object
        """
        if not search_key:
            return self.module.fail_json(
                msg='Must specify either a network name or id')
        network = clc_common.find_network(self.module, self.clc_auth,
                                          location,
                                          network_id_search=search_key,
                                          networks=self.networks)

        if network is None:
            changed = True
            if not self.module.check_mode:
                network = self._create_network(location)
        else:
            changed, network = self._update_network(location, network)

        return changed, network

    def _create_network(self, location):
        """
        Create a new network
        :param location: Datacenter in which to create network
        :return: Network object for newly created network, or response object
                 if wait parameter is false
        """
        params = self.module.params
        name = params.get('name', None)
        desc = params.get('description', None)

        try:
            response = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'POST', '/networks/{alias}/{location}/claim'.format(
                    alias=self.clc_auth['clc_alias'], location=location))
        except ClcApiException as e:
            return self.module.fail_json(
                msg='Unable to claim network in location: {location}. '
                    '{msg}'.format(location=location, msg=e.message))
        self._wait_for_requests([response])

        if params.get('wait'):
            try:
                operation_id = clc_common.operation_id_list([response])[0]
                response = clc_common.call_clc_api(
                    self.module, self.clc_auth,
                    'GET', '/operations/{alias}/status/{id}'.format(
                        alias=self.clc_auth['clc_alias'], id=operation_id))
                network_id = [r['id'] for r in response['summary']['links']
                              if r['rel'] == 'network'][0]
                network = clc_common.find_network(
                    self.module, self.clc_auth, location,
                    network_id_search=network_id)
            except ClcApiException as e:
                return self.module.fail_json(
                    msg='Unable to get network operation status for operation: '
                        '{id}. {message}'.format(
                            id=operation_id, message=e.message))
            if name is not None or desc is not None:
                changed, network = self._update_network(location, network)
            return network
        else:
            return response

    def _update_network(self, location, network):
        """
        Update Network within a datacenter
        :param location: Datacenter in which to update network
        :param network: Network object to update
        :return: Boolean indicating change, and network object
        """
        params = self.module.params

        changed = False
        name = params.get('name', None)
        desc = params.get('description', None)

        if (name is not None and network.name != name) or (
                desc is not None and network.description != desc):
            changed = True
            if not self.module.check_mode:

                update_name = name if name is not None else network.name
                update_desc = desc if desc is not None else network.description
                try:
                    # Returns 204 No Content
                    response = clc_common.call_clc_api(
                        self.module, self.clc_auth,
                        'PUT', '/networks/{alias}/{location}/{id}'.format(
                            alias=self.clc_auth['clc_alias'],
                            location=location, id=network.id),
                        data={'name': update_name, 'description': update_desc})
                except ClcApiException as e:
                    return self.module.fail_json(
                        msg='Unable to update network: {id} in location: '
                            '{location}. {msg}'.format(id=network.id,
                                                       location=location,
                                                       msg=e.message))
                network.name = network.data['name'] = update_name
                network.description = network.data['description'] = update_desc

        return changed, network

    def _delete_network(self, location, network):
        """
        Delete network within a datacenter
        :param location: Datacenter in which to update network
        :param network: Network object to deleted
        :return: none
        """
        try:
            # Returns 204 No Content
            response = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'POST', '/networks/{alias}/{location}/{id}/release'.format(
                    alias=self.clc_auth['clc_alias'], location=location,
                    id=network.id))
        except ClcApiException as e:
            return self.module.fail_json(
                msg='Unable to release network: {id} in location: {location}. '
                    '{msg}'.format(id=network.id, location=location,
                                   msg=e.message))

    def _wait_for_requests(self, request_list):
        """
        Block until server provisioning requests are completed.
        :param request_list: a list of CLC API JSON responses
        :return: none
        """
        if self.module.params.get('wait'):
            failed_requests_count = clc_common.wait_on_completed_operations(
                self.module, self.clc_auth,
                clc_common.operation_id_list(request_list))

            if failed_requests_count > 0:
                self.module.fail_json(msg='Unable to process network request')


def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
        argument_spec=ClcNetwork._define_module_argument_spec(),
        supports_check_mode=True)
    clc_network = ClcNetwork(module)
    clc_network.process_request()


from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
