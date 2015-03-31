#!/usr/bin/python

import sys
import os
import datetime
import json
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

class ClcPublicIp(object):
    clc = clc_sdk
    module = None
    group_dict = {}

    def __init__(self, module):

        self.module = module

        if not clc_found:
            self.module.fail_json(msg='clc-python-sdk required for this module')

    def process_request(self):
        p = self.module.params
        self._clc_set_credentials()

        server_ids = p['server_ids']
        ports = p['ports']
        protocol = p['protocol']
        requests = []

        servers = self.clc.v2.Servers(server_ids).servers
        ports_lst=[]
        for port in ports:
            ports_lst.append({'protocol': protocol, 'port': port})

        for server in servers:
            requests.append(server.PublicIPs().Add(ports_lst))

        sum(requests).WaitUntilComplete()

        #TODO:  Check requests status for failures, and either retry or exit with a failure

        servers_result = []
        servers = self.clc.v2.Servers(server_ids).servers
        for server in servers:
            if len(server.PublicIPs().public_ips) > 0:
                server.data['publicip'] = str(server.PublicIPs().public_ips[0])

            server.data['ipaddress'] = server.data['details']['ipAddresses'][0]['internal']
            servers_result.append(server.data)

        self.module.exit_json(changed=True, servers=servers_result, server_ids=server_ids)

    #
    #  Functions to define the Ansible module and its arguments
    #

    def _set_ansible_module(self):
        argument_spec = self.define_argument_spec()

        self.module = AnsibleModule(
            argument_spec=argument_spec
        )

    @staticmethod
    def define_argument_spec():
        argument_spec = dict(
            server_ids=dict(type='list', required=True),
            protocol=dict(default='TCP'),
            ports=dict(type='list', required=True)
            )
        return argument_spec

    #
    #   Module Behavior Functions
    #

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

def main():
    module = AnsibleModule(
            argument_spec=ClcPublicIp.define_argument_spec()
    )
    clcPublicIp = ClcPublicIp(module)
    clcPublicIp.process_request()


if __name__ == '__main__':
    main()