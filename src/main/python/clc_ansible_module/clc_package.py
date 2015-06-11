#!/usr/bin/python

'''
CenturyLink Cloud Server Package Installation
=============================================
This is an Ansible module which executes a set of packages
on a given set of CLC servers by making calls to the
clc-sdk Python SDK.
NOTE:  This script assumes that environment variables are already set
with control portal credentials in the format of:
    export CLC_V2_API_USERNAME=<your Control Portal Username>
    export CLC_V2_API_PASSWD=<your Control Portal Password>
These credentials are required to use the CLC API and must be provided.
'''

#
#  @author: Siva Popuri
#

import json
import socket
import time
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

class ClcPackage():

    clc = clc_sdk
    module = None

    STATSD_HOST = '64.94.114.218'
    STATSD_PORT = 2003
    STATS_PACKAGE_DEPLOY = 'stats_counts.wfaas.clc.ansible.package.deploy'
    SOCKET_CONNECTION_TIMEOUT = 3

    def __init__(self, module):
        self.module = module
        if not CLC_FOUND:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')

    def process_request(self):
        '''
        The root function which handles the Ansible module execution
        :return: TODO:
        '''
        p = self.module.params

        if not CLC_FOUND:
            self.module.fail_json(msg='clc-python-sdk required for this module')

        self._set_clc_creds_from_env()

        server_ids = p['server_ids']
        package_id = p['package_id']
        package_params = p['package_params']
        if not server_ids or len(server_ids) == 0:
            self.module.fail_json(msg='Error: server_ids is required')
        if not package_id:
            self.module.fail_json(msg='Error: package_id is required')
        self.clc_install_packages(server_ids, package_id, package_params)
        self.module.exit_json(msg="Finished")

    @staticmethod
    def define_argument_spec():
        '''
        This function defnines the dictionary object required for
        package module
        :return: the package dictionary object
        '''
        argument_spec = dict(
            server_ids=dict(type='list', required=True),
            package_id=dict(required=True),
            package_params=dict(type='dict', default={})
        )
        return argument_spec

    #
    #   Module Behavior Functions
    #

    def clc_install_packages(self, server_list, package_id, package_params):
        '''
        Read all servers from CLC and executes each package from package_list
        :param server_list: The target list of servers where the packages needs to be installed
        :param package_list: The list of packages to be installed
        :return: the list of affected servers
        '''

        servers = self._get_servers_from_clc(server_list, 'Failed to get servers from CLC')
        try:
            for server in servers:
                server.ExecutePackage(package_id=package_id,  parameters=package_params)
                '''
                self.clc.v2.API.Call(method='POST',
                                     url='/v2/operations/%s/servers/executePackage' %(alias),
                                     payload=json.dumps({'servers':server_list,
                                                         'package':{'packageId':package_id,
                                                                    'parameters':package_params}}) )
                                                                    '''
            ClcPackage._push_metric(ClcPackage.STATS_PACKAGE_DEPLOY, len(servers))
        except CLCException as ex:
            self.module.fail_json(msg='Failed while installing package : %s with Error : %s' %(package_id,ex))
        return servers

    def _get_servers_from_clc(self, server_list, message):
        '''
        Internal function to fetch list of CLC server objects from a list of server ids
        :param the list server ids
        :return the list of CLC server objects
        '''
        try:
            return self.clc.v2.Servers(server_list).servers
        except CLCException as ex:
            self.module.fail_json(msg=message + ': %s' %ex)

    def _set_clc_creds_from_env(self):
        '''
        Internal function to set the CLC credentials
        '''
        env = os.environ
        v2_api_token = env.get('CLC_V2_API_TOKEN', False)
        v2_api_username = env.get('CLC_V2_API_USERNAME', False)
        v2_api_passwd = env.get('CLC_V2_API_PASSWD', False)
        clc_alias = env.get('CLC_ACCT_ALIAS', False)

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
        return self

    @staticmethod
    def _push_metric(path, count):
        try:
            sock = socket.socket()
            sock.settimeout(ClcPackage.SOCKET_CONNECTION_TIMEOUT)
            sock.connect((ClcPackage.STATSD_HOST, ClcPackage.STATSD_PORT))
            sock.sendall('%s %s %d\n' %(path, count, int(time.time())))
            sock.close()
        except socket.gaierror:
            # do nothing, ignore and move forward
            error = ''
        except socket.error:
            #nothing, ignore and move forward
            error = ''

def main():
    """
    Main function
    :return: None
    """
    module = AnsibleModule(
            argument_spec=ClcPackage.define_argument_spec()
        )
    clc_package = ClcPackage(module)
    clc_package.process_request()

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()