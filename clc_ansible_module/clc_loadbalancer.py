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
module: clc_loadbalancer
short_description: Create, Delete shared loadbalancers in CenturyLink Cloud.
description:
  - An Ansible module to Create, Delete shared loadbalancers in CenturyLink Cloud.
version_added: "2.0"
options:
  name:
    description:
      - The name of the loadbalancer
    required: True
  description:
    description:
      - A description for the loadbalancer
    required: False
    default: None
  alias:
    description:
      - The alias of your CLC Account
    required: True
  location:
    description:
      - The location of the datacenter where the load balancer resides in
    required: True
  method:
    description:
      -The balancing method for the load balancer pool
    required: False
    default: None
    choices: ['leastConnection', 'roundRobin']
  persistence:
    description:
      - The persistence method for the load balancer
    required: False
    default: None
    choices: ['standard', 'sticky']
  port:
    description:
      - Port to configure on the public-facing side of the load balancer pool
    required: False
    default: None
    choices: [80, 443]
  nodes:
    description:
      - A list of nodes that needs to be added to the load balancer pool
    required: False
    default: []
  status:
    description:
      - The status of the loadbalancer
    required: False
    default: enabled
    choices: ['enabled', 'disabled']
  state:
    description:
      - Whether to create or delete the load balancer pool
    required: False
    default: present
    choices: ['present', 'absent', 'port_absent', 'nodes_present', 'nodes_absent']
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
- name: Create Loadbalancer
  hosts: localhost
  connection: local
  tasks:
    - name: Actually Create things
      clc_loadbalancer:
        name: test
        description: test
        alias: TEST
        location: WA1
        port: 443
        nodes:
          - { 'ipAddress': '10.11.22.123', 'privatePort': 80 }
        state: present

- name: Add node to an existing loadbalancer pool
  hosts: localhost
  connection: local
  tasks:
    - name: Actually Create things
      clc_loadbalancer:
        name: test
        description: test
        alias: TEST
        location: WA1
        port: 443
        nodes:
          - { 'ipAddress': '10.11.22.234', 'privatePort': 80 }
        state: nodes_present

- name: Remove node from an existing loadbalancer pool
  hosts: localhost
  connection: local
  tasks:
    - name: Actually Create things
      clc_loadbalancer:
        name: test
        description: test
        alias: TEST
        location: WA1
        port: 443
        nodes:
          - { 'ipAddress': '10.11.22.234', 'privatePort': 80 }
        state: nodes_absent

- name: Delete LoadbalancerPool
  hosts: localhost
  connection: local
  tasks:
    - name: Actually Delete things
      clc_loadbalancer:
        name: test
        description: test
        alias: TEST
        location: WA1
        port: 443
        nodes:
          - { 'ipAddress': '10.11.22.123', 'privatePort': 80 }
        state: port_absent

- name: Delete Loadbalancer
  hosts: localhost
  connection: local
  tasks:
    - name: Actually Delete things
      clc_loadbalancer:
        name: test
        description: test
        alias: TEST
        location: WA1
        port: 443
        nodes:
          - { 'ipAddress': '10.11.22.123', 'privatePort': 80 }
        state: absent
'''

RETURN = '''
changed:
    description: A flag indicating if any change was made or not
    returned: success
    type: boolean
    sample: True
loadbalancer:
    description: The load balancer result object from CLC
    returned: success
    type: dict
    sample:
        {
           "description":"test-lb",
           "id":"ab5b18cb81e94ab9925b61d1ca043fb5",
           "ipAddress":"66.150.174.197",
           "links":[
              {
                 "href":"/v2/sharedLoadBalancers/wfad/wa1/ab5b18cb81e94ab9925b61d1ca043fb5",
                 "rel":"self",
                 "verbs":[
                    "GET",
                    "PUT",
                    "DELETE"
                 ]
              },
              {
                 "href":"/v2/sharedLoadBalancers/wfad/wa1/ab5b18cb81e94ab9925b61d1ca043fb5/pools",
                 "rel":"pools",
                 "verbs":[
                    "GET",
                    "POST"
                 ]
              }
           ],
           "name":"test-lb",
           "pools":[

           ],
           "status":"enabled"
        }
'''

__version__ = '${version}'

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException


class ClcLoadBalancer(object):

    def __init__(self, module):
        """
        Construct module
        """
        self.clc_auth = {}
        self.module = module
        self.load_balancers = None

    def process_request(self):
        """
        Execute the main code path, and handle the request
        :return: none
        """
        p = self.module.params

        changed = False
        result_lb = None

        self.clc_auth = clc_common.authenticate(self.module)
        if p.get('alias') is None:
            p['alias'] = self.clc_auth['clc_alias']
        if p.get('description') is None:
            p['description'] = p.get('name')

        state = p.get('state')

        self.load_balancers = clc_common.loadbalancer_list(
            self.module, self.clc_auth,
            alias=p.get('alias'), location=p.get('location'))

        if state == 'present':
            changed, result_lb = self.ensure_loadbalancer_present()
        elif state == 'absent':
            changed, result_lb = self.ensure_loadbalancer_absent()

        elif state == 'port_absent':
            changed, result_lb = self.ensure_pool_absent()

        elif state == 'nodes_present':
            changed, result_lb = self.ensure_pool_nodes_present()
        elif state == 'nodes_absent':
            changed, result_lb = self.ensure_pool_nodes_absent()

        self.module.exit_json(changed=changed, loadbalancer=result_lb)

    def ensure_loadbalancer_present(self):
        """
        Checks to see if a load balancer exists and creates one if it does not.
        :return: (changed, result, lb_id)
            changed: Boolean whether a change was made
            loadbalancer: The result object from the CLC load balancer request
            lb_id: The load balancer id
        """
        p = self.module.params
        name = p.get('name')
        description = p.get('description')

        changed = False
        loadbalancer = self._find_loadbalancer(search_key=name)

        if not loadbalancer:
            if not self.module.check_mode:
                loadbalancer = self.create_loadbalancer()
            changed = True
        elif loadbalancer['description'] != description:
            if not self.module.check_mode:
                loadbalancer = self.update_loadbalancer(loadbalancer)
            changed = True

        if p.get('port'):
            changed, loadbalancer = self.ensure_pool_present(
                loadbalancer)
            if p.get('nodes'):
                changed, loadbalancer = self.ensure_pool_nodes_present(
                    loadbalancer)

        return changed, loadbalancer

    def ensure_loadbalancer_absent(self):
        """
        Checks to see if a load balancer exists and deletes it if it does
        :return: (changed, result)
            changed: Boolean whether a change was made
            result: The result from the CLC API Call
        """
        p = self.module.params
        name = p.get('name')

        changed = False
        result = None
        loadbalancer = self._find_loadbalancer(search_key=name)
        if loadbalancer:
            if not self.module.check_mode:
                result = self.delete_loadbalancer(loadbalancer)
            changed = True
        return changed, result

    def ensure_pool_present(self, loadbalancer):
        """
        Checks if a load balancer pool exists and creates one if it does not.
        :param loadbalancer: Loadbalancer object to check for pool existence
        :return: (changed, group, pool_id) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
            pool_id: The string id of the load balancer pool
        """
        p = self.module.params

        changed = False

        pool = self._find_pool(loadbalancer)
        if not pool:
            if not self.module.check_mode:
                result = self.create_pool(loadbalancer)
                loadbalancer = self._find_loadbalancer(
                    search_key=loadbalancer['id'], refresh=True)
            changed = True

        return changed, loadbalancer

    def ensure_pool_absent(self):
        """
        Checks to see if a load balancer pool exists and deletes it if it does
        :return: (changed, result) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        p = self.module.params
        name = p.get('name')

        changed = False
        loadbalancer = self._find_loadbalancer(search_key=name)
        if loadbalancer:
            pool = self._find_pool(loadbalancer)
            if pool:
                if not self.module.check_mode:
                    result = self.delete_pool(loadbalancer, pool)
                    loadbalancer = self._find_loadbalancer(
                        search_key=loadbalancer['id'], refresh=True)
                changed = True
        else:
            return self.module.fail_json(
                msg='No load balancers matching: {search}.'.format(search=name))
        return changed, loadbalancer

    def ensure_pool_nodes_present(self, loadbalancer=None):
        """
        Checks if list of nodes exist on pool and adds if they don't exist
        :param loadbalancer: Loadbalancer on which to check nodes
        :return: (changed, result) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        p = self.module.params
        name = p.get('name')
        nodes = p.get('nodes')
        for node in nodes:
            if not node.get('status'):
                node['status'] = 'enabled'

        if loadbalancer is None:
            loadbalancer = self._find_loadbalancer(search_key=name)

        changed = False
        if loadbalancer:
            pool = self._find_pool(loadbalancer)
            if not pool:
                pool = self.create_pool(loadbalancer)
            result = pool
            updated_nodes = self._update_node_list(pool['nodes'])
            if updated_nodes != pool['nodes']:
                changed = True
                if not self.module.check_mode:
                    result = self._update_pool_nodes(loadbalancer, pool,
                                                     updated_nodes)
                    loadbalancer = self._find_loadbalancer(
                        search_key=loadbalancer['id'], refresh=True)
        else:
            return self.module.fail_json(
                msg='No load balancers matching: {search}.'.format(search=name))

        return changed, loadbalancer

    def ensure_pool_nodes_absent(self, loadbalancer=None):
        """
        Checks if list of nodes not on pool and remove if they do exist
        :param loadbalancer: Loadbalancer on which to check nodes
        :return: (changed, result) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        p = self.module.params
        name = p.get('name')

        if loadbalancer is None:
            loadbalancer = self._find_loadbalancer(search_key=name)

        changed = False
        if loadbalancer:
            pool = self._find_pool(loadbalancer)
            result = pool
            if pool:
                updated_nodes = self._update_node_list(pool['nodes'],
                                                       remove_nodes=True)
                if updated_nodes != pool['nodes']:
                    changed = True
                    if not self.module.check_mode:
                        result = self._update_pool_nodes(loadbalancer, pool,
                                                         updated_nodes)
                        loadbalancer = self._find_loadbalancer(
                            search_key=loadbalancer['id'], refresh=True)
        else:
            return self.module.fail_json(
                msg='No load balancers matching: {search}.'.format(search=name))
        return changed, loadbalancer

    def create_loadbalancer(self):
        """
        Create a loadbalancer w/ params
        :return: result: The result from the CLC API call
        """
        p = self.module.params
        alias = p.get('alias')
        location = p.get('location')
        name = p.get('name')

        if not clc_common.server_ids_in_datacenter(self.module, self.clc_auth,
                                                   location, alias=alias):
            self.module.fail_json(
                msg='Cannot create load balancer for account: {alias} '
                    'in location: {location}. No servers are present in '
                    'datacenter.'.format(
                        alias=alias, location=location))

        result = None
        try:
            result = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'POST', '/sharedLoadBalancers/{alias}/{location}'.format(
                    alias=alias, location=location),
                data={'name': name,
                      'description': p.get('description'),
                      'status': p.get('status')},
                timeout=60)
        except ClcApiException as e:
            self.module.fail_json(
                msg='Unable to create load balancer with name: {name} '
                    'for account: {alias} in location: {location}. '
                    '{msg}'.format(name=name, alias=alias, location=location,
                                   msg=e.message))
        return result

    def delete_loadbalancer(self, loadbalancer):
        """
        Delete CLC loadbalancer
        :param loadbalancer: Loadbalancer object to delete
        :return: result: The result from the CLC API call
        """
        p = self.module.params
        alias = p.get('alias')
        location = p.get('location')

        try:
            # Returns 204 No Content
            result = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'DELETE', '/sharedLoadBalancers/{alias}/{location}/{id}'.format(
                    alias=alias, location=location, id=loadbalancer['id']),
                timeout=60)
        except ClcApiException as e:
            return self.module.fail_json(
                msg='Unable to delete load balancer with name: {name}. '
                    '{msg}'.format(name=loadbalancer['name'], msg=e.message))
        return result

    def update_loadbalancer(self, loadbalancer):
        """
        Update CLC loadbalancer
        :param loadbalancer: Loadbalancer object to delete
        :return: result: The result from the CLC API call
        """
        p = self.module.params
        alias = p.get('alias')
        location = p.get('location')
        name = p.get('name')
        description = p.get('description')

        try:
            # Returns 204 No Content
            result = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'PUT', '/sharedLoadBalancers/{alias}/{location}/{id}'.format(
                    alias=alias, location=location, id=loadbalancer['id']),
                data={'name': name,
                      'description': description},
                timeout=60)
        except ClcApiException as e:
            return self.module.fail_json(
                msg='Unable to update load balancer with name: {name}. '
                    '{msg}'.format(name=loadbalancer['name'], alias=alias,
                                   location=location, msg=e.message))
        return result

    def create_pool(self, loadbalancer):
        """
        Creates a pool on the provided load balancer
        :param loadbalancer: Loadbalancer object to modify
        :return: result: The result from the create API call
        """
        p = self.module.params
        alias = p.get('alias')
        location = p.get('location')

        try:
            result = clc_common.call_clc_api(
                self.module, self.clc_auth, 'POST',
                '/sharedLoadBalancers/{alias}/{location}/{id}/pools'.format(
                    alias=alias, location=location, id=loadbalancer['id']),
                data={'port': p.get('port'),
                      'method': p.get('method'),
                      'persistence': p.get('persistence')},
                timeout=60)
        except ClcApiException as e:
            return self.module.fail_json(
                msg='Unable to create pool for load balancer with '
                    'name: {name}. {msg}'.format(name=loadbalancer['name'],
                                                 msg=e.message))
        return result

    def delete_pool(self, loadbalancer, pool):
        """
        Delete the pool on the provided load balancer
        :param loadbalancer: Loadbalancer object to modify
        :param pool: Loadbalancer pool to delete
        :return: result: The result from the delete API call
        """
        p = self.module.params
        alias = p.get('alias')
        location = p.get('location')

        try:
            # Returns 204 No Content
            result = clc_common.call_clc_api(
                self.module, self.clc_auth, 'DELETE',
                '/sharedLoadBalancers/{alias}/{location}/{lb_id}'
                '/pools/{pool_id}'.format(alias=alias, location=location,
                                          lb_id=loadbalancer['id'],
                                          pool_id=pool['id']),
                timeout=60)
        except ClcApiException as e:
            return self.module.fail_json(
                msg='Unable to delete pool on port: {port} for load balancer '
                    'with name: {name}. {msg}'.format(
                        port=pool['port'], name=loadbalancer['name'],
                        msg=e.message))
        return result

    def _update_pool_nodes(self, loadbalancer, pool, node_list):
        """
        Update list of nodes in loadbalancer pool
        :param loadbalancer: Loadbalancer on which to update nodes
        :param pool: Pool to be updated
        :param node_list: List/set of nodes
        :return:
        """
        p = self.module.params
        alias = p.get('alias')
        location = p.get('location')

        try:
            # Returns 204 No Content
            result = clc_common.call_clc_api(
                self.module, self.clc_auth, 'PUT',
                '/sharedLoadBalancers/{alias}/{location}/{lb_id}'
                '/pools/{pool_id}/nodes'.format(
                    alias=alias, location=location,
                    lb_id=loadbalancer['id'], pool_id=pool['id']),
                data=node_list,
                timeout=60)
        except ClcApiException as e:
            return self.module.fail_json(
                msg='Unable to updated nodes in pool on port: {port} '
                    'for load balancer with name: {name}. {msg}'.format(
                        port=pool['port'], name=loadbalancer['name'],
                        msg=e.message))
        return result

    def _find_loadbalancer(self, search_key=None, refresh=False):
        """
        Retrieves load balancer matching search key
        :param search_key: Id or name of load balancer
        :param refresh: Boolean on whether to refresh the data
        :return: Matching load balancer dictionary
        """
        alias = self.module.params.get('alias')
        location = self.module.params.get('location')
        if refresh:
            self.load_balancers = clc_common.loadbalancer_list(
                self.module, self.clc_auth, alias=alias, location=location)
        loadbalancer = clc_common.find_loadbalancer(
            self.module, self.clc_auth, search_key,
            load_balancers=self.load_balancers)
        return loadbalancer

    def _find_pool(self, loadbalancer):
        p = self.module.params
        port = int(p.get('port'))

        result = None
        for pool in loadbalancer['pools']:
            if int(pool['port']) == port:
                result = pool
        return result

    def _update_node_list(self, existing_nodes, remove_nodes=False):
        """
        Update list of existing nodes to nodes specified in module call
        All nodes passed back are a shallow copy of the original node
        :param existing_nodes: List of existing nodes
        :param remove_nodes: bool indicating whether to remove nodes
        :return: Updated list of dictionaries
        """
        p = self.module.params
        nodes = p.get('nodes')

        updated_nodes = []
        nodes_dict = dict([(n['ipAddress'], n) for n in nodes])
        for node in existing_nodes:
            ip = node['ipAddress']
            if ip in nodes_dict:
                if remove_nodes:
                    continue
                else:
                    new_node = node.copy()
                    new_node.update(nodes_dict[ip])
                    updated_nodes.append(new_node)
            else:
                updated_nodes.append(node.copy())
        if not remove_nodes:
            existing_ips = [n['ipAddress'] for n in updated_nodes]
            for node in nodes:
                if node['ipAddress'] not in existing_ips:
                    updated_nodes.append(node.copy())
        return updated_nodes

    @staticmethod
    def define_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            name=dict(required=True),
            description=dict(default=None),
            location=dict(required=True),
            alias=dict(required=False),
            port=dict(type='int', choices=[80, 443]),
            method=dict(choices=['leastConnection', 'roundRobin'],
                        default='roundRobin'),
            persistence=dict(choices=['standard', 'sticky'],
                             default='standard'),
            nodes=dict(type='list', default=[]),
            status=dict(default='enabled', choices=['enabled', 'disabled']),
            state=dict(
                default='present',
                choices=[
                    'present',
                    'absent',
                    'port_absent',
                    'nodes_present',
                    'nodes_absent'])
        )
        return argument_spec


def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(argument_spec=ClcLoadBalancer.define_argument_spec(),
                           supports_check_mode=True)
    clc_loadbalancer = ClcLoadBalancer(module)
    clc_loadbalancer.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
