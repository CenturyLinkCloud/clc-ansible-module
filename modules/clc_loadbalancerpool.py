#!/usr/bin/python
DOCUMENTATION = '''
module: clc_loadbalancerpool
short_description: Create/delete Load Balancer Pools and nodes at CenturyLink Cloud
description:
  - Create or delete Load balancer Pools and nodes at CenturyLink Cloud
options:
  alias:
    description:
      - The alias of your CLC Account
  location:
    description:
      - The location of the datacenter your load balancer resides in
  loadbalancer:
    description:
      - The name of the load balancer you want to modify
  method:
    description:
      -The balancing method for this pool
    default: roundRobin
    choices: ['sticky', 'roundRobin']
  persistence:
    description:
      - The persistence method for this load balancer
    default: standard
    choices: ['standard', 'sticky']
  port:
    description:
      - Port to configure on the public-facing side of the load balancer pool
    choices: [80, 443]
  nodes:
    description:
      - A list of nodes that you want added to your load balancer pool
  state:
    description:
      - Whether to create or delete the load balancer pool
    default: present
    choices: ['present', 'absent']
'''

EXAMPLES = '''

# Create a new Empty Load Balancer Pool

---
- name: Create Load Balancer Pool
  hosts: localhost
  connection: local
  gather_facts: False
  tasks:
    - name: Create new Load Balancer Pool
      clc_loadbalancerpool:
        alias: WFAD
        location: WA1
        loadbalancer: TEST
        port: 80
        state: present

# Create a new Load Balancer Pool with nodes

---
- name: Create Load Balancer Pool
  hosts: localhost
  connection: local
  gather_facts: False
  tasks:
    - name: Create new Load Balancer Pool
      clc_loadbalancerpool:
        alias: WFAD
        location: WA1
        loadbalancer: TEST
        port: 80
        nodes:
          - { 'ipAddress': '10.11.12.123', 'privatePort': 80 }
          - { 'ipAddress': '10.11.12.124', 'privatePort': 80 }
        state: present

# Delete a Load Balancer Pool

---
- name: Create Load Balancer Pool
  hosts: localhost
  connection: local
  gather_facts: False
  tasks:
    - name: Create new Load Balancer Pool
      clc_loadbalancerpool:
        alias: WFAD
        location: WA1
        loadbalancer: TEST
        port: 80
        state: absent

'''

import sys
import os
import datetime
import json

#
#  Requires the clc-python-sdk.
#  sudo pip install clc-sdk
#
try:
    import clc as clc_sdk
    from clc import CLCException
except ImportError:
    CLC_FOUND = False
    clc_sdk = None
else:
    CLC_FOUND = True


class ClcLoadBalancerPool():

    clc = None

    def __init__(self, module):
        """
        Construct module
        """
        self.clc = clc_sdk
        self.module = module
        self.lb_dict = {}

        if not CLC_FOUND:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')

    def process_request(self):
        """
        Execute the main code path, and handle the request
        :return: none
        """

        loadbalancerpool_alias=self.module.params.get('alias')
        loadbalancerpool_location=self.module.params.get('location')
        loadbalancerpool_loadbalancer=self.module.params.get('loadbalancer')
        loadbalancerpool_method=self.module.params.get('method')
        loadbalancerpool_persistence=self.module.params.get('persistence')
        loadbalancerpool_port=self.module.params.get('port')
        loadbalancerpool_nodes=self.module.params.get('nodes')
        state=self.module.params.get('state')

        self.set_clc_credentials_from_env()

        self.lb_dict = self._get_loadbalancer_list(alias=loadbalancerpool_alias, location=loadbalancerpool_location)

        if state == 'present':
            changed, result = self.ensure_loadbalancerpool_present(alias=loadbalancerpool_alias,
                                                                   location=loadbalancerpool_location,
                                                                   loadbalancer=loadbalancerpool_loadbalancer,
                                                                   method=loadbalancerpool_method,
                                                                   persistence=loadbalancerpool_persistence,
                                                                   port=loadbalancerpool_port,
                                                                   nodes=loadbalancerpool_nodes)
            self.module.exit_json(changed=changed, loadbalancerpool=result)
        elif state == 'absent':
            changed, result = self.ensure_loadbalancerpool_absent(alias=loadbalancerpool_alias,
                                                                  location=loadbalancerpool_location,
                                                                  loadbalancer=loadbalancerpool_loadbalancer,
                                                                  port=loadbalancerpool_port)
            self.module.exit_json(changed=changed, loadbalancerpool=result)

    #
    #  Functions to define the Ansible module and its arguments
    #

    def ensure_loadbalancerpool_present(self, alias, location, loadbalancer, method, persistence, port, nodes):
        """
        Checks to see if a load balancer pool exists and creates one if it does not.
        :param alias: The account alias
        :param location: the datacenter the load balancer resides in
        :param loadbalancer: the name of the load balancer
        :param method: the load balancing method
        :param persistence: the load balancing persistence type
        :param port: the port that the load balancer will listen on
        :param nodes: a list of dictionaries containing any nodes that the load balancer should send traffic to
        :return: (changed, group) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        changed = False

        lb_exists = self._loadbalancer_exists(loadbalancer=loadbalancer)
        if lb_exists:
            lb_id = self._get_loadbalancer_id(loadbalancer=loadbalancer)
            pool_id = self._loadbalancerpool_exists(alias=alias, location=location, port=port, lb_id=lb_id)
            if not pool_id:
                changed = True
                result = self.create_loadbalancerpool(alias=alias, location=location, lb_id=lb_id, method=method, persistence=persistence, port=port)
                if nodes:
                    pool_id = self._loadbalancerpool_exists(alias=alias, location=location, port=port, lb_id=lb_id)
                    self.add_loadbalancernodes(alias=alias, location=location, lb_id=lb_id, pool_id=pool_id, nodes=nodes)
            else:
                changed = False
                result = port
        else:
            result = "LB Doesn't Exist"
        return changed, result

    def ensure_loadbalancerpool_absent(self, alias, location, loadbalancer, port):
        """
        Checks to see if a load balancer pool exists and deletes it if it does
        :param alias: The account alias
        :param location: the datacenter the load balancer resides in
        :param loadbalancer: the name of the load balancer
        :param port: the port that the load balancer will listen on
        :return: (changed, group) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        changed = False

        lb_exists = self._loadbalancer_exists(loadbalancer=loadbalancer)
        if lb_exists:
            lb_id = self._get_loadbalancer_id(loadbalancer=loadbalancer)
            pool_id = self._loadbalancerpool_exists(alias=alias, location=location, port=port, lb_id=lb_id)
            if pool_id:
                changed = True
                result = self.delete_loadbalancerpool(alias=alias, location=location, lb_id=lb_id, pool_id=pool_id)
            else:
                changed = False
                result = "Pool doesn't exist"
        else:
            result = "LB Doesn't Exist"
        return changed, result

    def create_loadbalancerpool(self, alias, location, lb_id, method, persistence, port):
        """
        Creates a pool on the provided load balancer
        :param alias: the account alias
        :param location: the datacenter the load balancer resides in
        :param lb_id: the id string of the load balancer
        :param method: the load balancing method
        :param persistence: the load balancing persistence type
        :param port: the port that the load balancer will listen on
        :return: result: The result from the create API call
        """
        result = self.clc.v2.API.Call('POST', '/v2/sharedLoadBalancers/%s/%s/%s/pools' % (alias, location, lb_id), json.dumps({"port":port, "method":method, "persistence":persistence}))
        return result

    def delete_loadbalancerpool(self, alias, location, lb_id, pool_id):
        """
        Delete a pool on the provided load balancer
        :param alias: The account alias
        :param location: the datacenter the load balancer resides in
        :param lb_id: the id string of the load balancer
        :param pool_id: the id string of the pool
        :return: result: The result from the delete API call
        """
        result = self.clc.v2.API.Call('DELETE', '/v2/sharedLoadBalancers/%s/%s/%s/pools/%s' % (alias, location, lb_id, pool_id))
        return result

    def add_loadbalancernodes(self, alias, location, lb_id, pool_id, nodes):
        """
        Adds nodes to the provided pool
        :param alias: the account alias
        :param location: the datacenter the load balancer resides in
        :param lb_id: the id string of the load balancer
        :param pool_id: the id string of the pool
        :param nodes: a list of dictionaries containing the nodes to add
        :return: result: The result from the API call
        """
        result = self.clc.v2.API.Call('PUT', '/v2/sharedLoadBalancers/%s/%s/%s/pools/%s/nodes' % (alias, location, lb_id, pool_id), json.dumps(nodes))
        return result


    def _get_loadbalancer_list(self, alias, location):
        """
        Gets a list of all load balancers in a given datacenter for a given alias
        :param alias: the account alias
        :param location: the datacenter to search in
        :return: A list of dictionaries containing all applicable load balancers
        """
        return self.clc.v2.API.Call(method='GET', url='/v2/sharedLoadBalancers/%s/%s' % (alias, location))

    def _loadbalancer_exists(self, loadbalancer):
        """
        Checks to see if a given load balancer name exists alread
        :param loadbalancer: the name of the load balancer
        :return: result: True of False
        """
        result = False
        id = False
        if loadbalancer in [lb.get('name') for lb in self.lb_dict]:
            result = True
        return result

    def _get_loadbalancer_id(self, loadbalancer):
        """
        Retrieves the string id of the provided load balanacer
        :param loadbalancer: the name of the load balancer
        :return: id: the string id of the provided load balancer
        """
        for lb in self.lb_dict:
            if lb.get('name') == loadbalancer:
                id = lb.get('id')
        return id


    def _loadbalancerpool_exists(self, alias, location, port, lb_id):
        """
        Checks to see if a pool exists on the specified port on the provided load balancer
        :param alias: the account alias
        :param location: the datacenter the load balancer resides in
        :param port: the port to check and see if it exists
        :param lb_id: the id string of the provided load balancer
        :return: result: The id string of the pool or False
        """
        result = False
        pool_id = False
        pool_list = self.clc.v2.API.Call('GET', '/v2/sharedLoadBalancers/%s/%s/%s/pools' % (alias, location, lb_id))
        for pool in pool_list:
            if int(pool.get('port')) == int(port):
                result = pool.get('id')

        return result

    @staticmethod
    def define_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            location=dict(required=True, default=None),
            alias=dict(required=True, default=None),
            loadbalancer=dict(required=True),
            method=dict(choices=['leastConnection', 'roundRobin']),
            persistence=dict(choices=['standard', 'sticky']),
            port=dict(required=True, choices=[80, 443]),
            nodes=dict(type='list', default=[]),
            state=dict(default='present', choices=['present', 'absent'])
        )

        return argument_spec

    #
    #   Module Behavior Functions
    #

    def set_clc_credentials_from_env(self):
        """
        Set the CLC Credentials on the sdk by reading environment variables
        :return: none
        """
        env = os.environ
        v2_api_token = env.get('CLC_V2_API_TOKEN', False)
        v2_api_username = env.get('CLC_V2_API_USERNAME', False)
        v2_api_passwd = env.get('CLC_V2_API_PASSWD', False)

        if v2_api_token:
            self.clc._LOGIN_TOKEN_V2 = v2_api_token
        elif v2_api_username and v2_api_passwd:
            self.clc.v2.SetCredentials(
                api_username=v2_api_username,
                api_passwd=v2_api_passwd)
        else:
            return self.module.fail_json(
                msg="You must set the CLC_V2_API_USERNAME and CLC_V2_API_PASSWD "
                    "environment variables")

def main():
    module = AnsibleModule(argument_spec=ClcLoadBalancerPool.define_argument_spec())

    clc_loadbalancerpool = ClcLoadBalancerPool(module)
    clc_loadbalancerpool.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
