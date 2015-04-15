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

class ClcPackage():

    clc = None

    def __init__(self, module):
        self.clc = clc_sdk
        self.module = module

    def process_request(self):
        p = self.module.params

        if not clc_found:
            self.module.fail_json(msg='clc-python-sdk required for this module')

        self.set_clc_credentials_from_env()

        server_ids = p['server_ids']
        packages = p['packages']
        state = p['state']

    @staticmethod
    def define_argument_spec():
        package = dict(
            package_id=dict(required=True),
            parameters=dict(type="list")
        )
        argument_spec = dict(
            server_ids=dict(type='list', required=True),
            packages=dict(dict(package_id=dict(required=True), pamrameters=dict(type="list")), type='list', required=True),
            state=dict(default='present', choices=['present', 'absent'])
        )
        return argument_spec

    #
    #   Module Behavior Functions
    #

    def clc_install_packages(self, server_list, package_list):
        servers = self._get_servers_from_clc(server_list, 'Failed to get servers from CLC')
        try:
            for package in package_list:
                servers.ExecutePackage(package_id=package.package_id,  parameters=package.parameters)
        except CLCException as ex:
            self.module.fail_json('Failed while installing package : %s with Error : %s' %(package,ex))
        return servers

    def _get_servers_from_clc(self, server_list, message):
        try:
            return self.clc.v2.Servers(server_list).servers
        except CLCException as ex:
            self.module.fail_json(msg=message + '%s' %ex)

    def _set_clc_creds_from_env(self):
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
        return self

def main():
    module = AnsibleModule(
            argument_spec=ClcPackage.define_argument_spec()
        )
    clc_package = ClcPackage(module)
    clc_package.process_request()


if __name__ == '__main__':
    main()