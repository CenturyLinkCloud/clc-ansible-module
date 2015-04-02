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


    def process_request(self, params):
        p = params
        self.set_clc_credentials_from_env()
        server_ids = p['server_ids']
        ports = p['ports']
        protocol = p['protocol']

        try:
            servers = self.clc.v2.Servers(server_ids).servers
        except CLCException, e:
            return self.module.fail_json(msg="Failed obtain server list from the CLC API: %s" % e)

        ports_lst = []
        requests_lst = []
        for port in ports: ports_lst.append({'protocol': protocol, 'port': port})
        for server in servers: requests_lst.append(server.PublicIPs().Add(ports_lst))
        for request in requests_lst: request.WaitUntilComplete()

        #TODO:  Check requests status for failures, and either retry or exit with a failure
        servers_result = []
        try:
            servers = self.clc.v2.Servers(server_ids).servers
        except CLCException, e:
            return self.module.fail_json(msg="Failed refresh server list from CLC API: %s" % e)

        for server in servers:
            if len(server.PublicIPs().public_ips) > 0: server.data['publicip'] = str(server.PublicIPs().public_ips[0])
            server.data['ipaddress'] = server.data['details']['ipAddresses'][0]['internal']
            servers_result.append(server.data)

        self.module.exit_json(changed=True, servers=servers_result, server_ids=server_ids)


    @staticmethod
    def define_argument_spec():
        argument_spec = dict(
            server_ids=dict(type='list', required=True),
            protocol=dict(default='TCP'),
            ports=dict(type='list', required=True)
            )
        return argument_spec


    def set_clc_credentials_from_env(self):
            e = os.environ
            v2_api_passwd = None
            v2_api_username = None
            try:
                v2_api_username = e['CLC_V2_API_USERNAME']
                v2_api_passwd = e['CLC_V2_API_PASSWD']
            except KeyError, e:
                return self.module.fail_json(msg = "You must set the CLC_V2_API_USERNAME and CLC_V2_API_PASSWD environment variables")

            self.clc.v2.SetCredentials(api_username=v2_api_username, api_passwd=v2_api_passwd)


def main():
    module = AnsibleModule(
        argument_spec=ClcPublicIp.define_argument_spec()
    )
    clcPublicIp = ClcPublicIp(module)
    clcPublicIp.process_request(module.params)


if __name__ == '__main__':
    main()