#!/usr/bin/python
DOCUMENTATION = '''

'''

EXAMPLES = '''


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
        state=self.module.params.get('state')

        self.set_clc_credentials_from_env()

        self.lb_dict = self._get_loadbalancer_list(alias=loadbalancerpool_alias, location=loadbalancerpool_location)

        if state == 'present':
            changed, result = self.ensure_loadbalancerpool_present(alias=loadbalancerpool_alias,
                                                                   location=loadbalancerpool_location,
                                                                   loadbalancer=loadbalancerpool_loadbalancer,
                                                                   method=loadbalancerpool_method,
                                                                   persistence=loadbalancerpool_persistence,
                                                                   port=loadbalancerpool_port)
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

    def ensure_loadbalancerpool_present(self, alias, location, loadbalancer, method, persistence, port):
        changed = False

        lb_exists = self._loadbalancer_exists(loadbalancer=loadbalancer)
        if lb_exists:
            lb_id = self._get_loadbalancer_id(loadbalancer=loadbalancer)
            pool_id = self._loadbalancerpool_exists(alias=alias, location=location, port=port, lb_id=lb_id)
            if not pool_id:
                changed = True
                result = self.create_loadbalancerpool(alias=alias, location=location, lb_id=lb_id, method=method, persistence=persistence, port=port)
            else:
                changed = False
                result = port
            return changed, result

    def ensure_loadbalancerpool_absent(self, alias, location, loadbalancer, port):
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
            return changed, result

    def create_loadbalancerpool(self, alias, location, lb_id, method, persistence, port):
        result = self.clc.v2.API.Call('POST', '/v2/sharedLoadBalancers/%s/%s/%s/pools' % (alias, location, lb_id), json.dumps({"port":port, "method":method, "persistence":persistence}))
        return result

    def delete_loadbalancerpool(self, alias, location, lb_id, pool_id):
        result = self.clc.v2.API.Call('DELETE', '/v2/sharedLoadBalancers/%s/%s/%s/pools/%s' % (alias, location, lb_id, pool_id))
        return result

    def _get_loadbalancer_list(self, alias, location):
        return self.clc.v2.API.Call('GET', '/v2/sharedLoadBalancers/%s/%s' % (alias, location))

    def _loadbalancer_exists(self, loadbalancer):
        result = False
        id = False
        if loadbalancer in [lb.get('name') for lb in self.lb_dict]:
            result = True
        return result

    def _get_loadbalancer_id(self, loadbalancer):
        for lb in self.lb_dict:
            if lb.get('name') == loadbalancer:
                id = lb.get('id')
        return id


    def _loadbalancerpool_exists(self, alias, location, port, lb_id):
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
            port=dict(required=True, choices=['80', '443']),
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
