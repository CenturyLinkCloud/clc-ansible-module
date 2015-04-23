#!/usr/bin/python

"""
CenturyLink Cloud Server Snapshot
=================================
This is an Ansible module which can be used to create
a snapshot of a CLC server
This module expects the below list of arguments to be used in playbook
    server_ids : the list of server ids to perform create snapshot operation on
    expiration_days : the no.of days to keep the snapshot (must be between 1 and 10)
    wait : True/False flag indicating weather to wait until the snapshot job finishes.
           It is an optional argument. The default value is 'True'
NOTE:  This script assumes that environment variables are already set
with control portal credentials in the format of:
    export CLC_V2_API_USERNAME=<your Control Portal Username>
    export CLC_V2_API_PASSWD=<your Control Portal Password>
These credentials are required to use the CLC API and must be provided.
"""

#
#  @author: Siva Popuri
#

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

class ClcSnapshot():

    clc = None

    def __init__(self, module):
        self.clc = clc_sdk
        self.module = module

    def process_request(self):
        """
        The root function which handles the Ansible module execution
        :return: TODO:
        """
        p = self.module.params

        if not clc_found:
            self.module.fail_json(msg='clc-python-sdk required for this module')

        self._set_clc_creds_from_env()

        server_ids = p['server_ids']
        expiration_days = p['expiration_days']
        wait = p['wait']
        acct_alias = self.clc.v2.Account.GetAlias()
        result = self.clc_create_snapshot(acct_alias, server_ids, expiration_days, wait)
        self.module.exit_json(result)

    @staticmethod
    def define_argument_spec():
        """
        This function defnines the dictionary object required for
        package module
        :return: the package dictionary object
        """
        argument_spec = dict(
            server_ids=dict(type='list', required=True),
            expiration_days=dict(required=True),
            wait=dict(default=True)
        )
        return argument_spec

    #
    #   Module Behavior Functions
    #

    def clc_create_snapshot(self, acct_alias, server_list, expiration_days, wait):
        """
        Create a snapshot for the given list of servers
        :param server_list: The target list of servers where the packages needs to be installed
        :param expiration_days: the number of days to keep the snapshot
        :param True/False indicating weather to wait until the snapshot action is finished
        :return: the result of snapshot job
        """

        servers = self._get_servers_from_clc(server_list, 'Failed to get servers from CLC')
        try:
            #server.CreateSnapshot(delete_existing=True, expiration_days=expiration_days)
            res = self.clc.v2.API.Call('POST','/v2/operations/%s/servers/createSnapshot' % (acct_alias), json.dumps({'serverIds': server_list, 'snapshotExpirationDays': expiration_days}))
            result = self.clc.v2.Requests(res)
            if wait:
                result.waitUntilFinished()
        except CLCException as ex:
            self.module.fail_json(msg='Failed to create snap shot with Error : %s' %(ex))
        return result

    def _get_servers_from_clc(self, server_list, message):
        """
        Internal function to fetch list of CLC server objects from a list of server ids
        :param the list server ids
        :return the list of CLC server objects
        """
        try:
            return self.clc.v2.Servers(server_list).servers
        except CLCException as ex:
            self.module.fail_json(msg=message + '%s' %ex)

    def _set_clc_creds_from_env(self):
        """
        Internal function to set the CLC credentials
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
        return self

def main():
    """
    Main function
    :return: None
    """
    module = AnsibleModule(
            argument_spec=ClcSnapshot.define_argument_spec()
        )
    clc_snapshot = ClcSnapshot(module)
    clc_snapshot.process_request()


if __name__ == '__main__':
    main()