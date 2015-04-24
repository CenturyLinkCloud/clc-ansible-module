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
        state = p['state']
        command_list = []

        acct_alias = self.clc.v2.Account.GetAlias()
        if state == 'present':
            command_list.append(
                lambda: self.clc_create_servers_snapshot(
                    server_ids=server_ids,
                    expiration_days=expiration_days))
        elif state == 'absent':
            command_list.append(
                lambda: self.clc_delete_servers_snapshot(
                    server_ids=server_ids))
        elif state == 'restore':
            command_list.append(
                lambda: self.clc_restore_servers_snapshot(
                    server_ids=server_ids))
        else:
            return self.module.fail_json(msg="Unknown State: " + state)

        has_made_changes, result_servers = self.run_clc_commands(
            command_list)
        return self.module.exit_json(
            changed=has_made_changes,
            servers=result_servers)
        #result = self.clc_ensure_snapshot(acct_alias, server_ids, expiration_days, state, wait)
        #self.module.exit_json(msg="Finished processing the snapshot request!!!")

    def run_clc_commands(self, command_list):
        requests_list = []
        changed_servers = []
        for command in command_list:
            requests, servers = command()
            requests_list += requests
            changed_servers += servers
        self._wait_for_requests_to_complete(requests_list)
        has_made_changes, result_changed_servers = self._parse_server_results(
            changed_servers)
        return has_made_changes, result_changed_servers

    def _wait_for_requests_to_complete(self, requests_lst, action='create'):
        for request in requests_lst:
            request.WaitUntilComplete()
            for request_details in request.requests:
                if request_details.Status() != 'succeeded':
                    self.module.fail_json(
                        msg='Unable to ' +
                        action +
                        ' Public IP for ' +
                        request.server.id +
                        ': ' +
                        request.Status())

    @staticmethod
    def _parse_server_results(servers):
        servers_result = []
        changed = False
        snapshot = ''
        for server in servers:
            has_snapshot = len(server.GetSnapshots()) > 0
            if has_snapshot:
                changed = True
                snapshot = str(server.GetSnapshots()[0])
            ipaddress = server.data['details']['ipAddresses'][0]['internal']
            server.data['ipaddress'] = ipaddress
            server.data['snapshot'] = snapshot
            servers_result.append(server.data)
        return changed, servers_result

    def _get_servers_from_clc_api(self, server_ids, message):
        try:
            return self.clc.v2.Servers(server_ids).servers
        except CLCException as exception:
            self.module.fail_json(msg=message + ': %s' % exception)

    def _get_servers_from_clc_api(self, server_ids, message):
        try:
            return self.clc.v2.Servers(server_ids).servers
        except CLCException as exception:
            self.module.fail_json(msg=message + ': %s' % exception)

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
            wait=dict(default=True),
            state=dict(default='present', choices=['present', 'absent', 'restore']),
        )
        return argument_spec

    #
    #   Module Behavior Functions
    #

    def clc_create_server_snapshot(self, acct_alias, server_id, expiration_days):
        try:
            server = self.clc.v2.Server(server_id)
            res = server.CreateSnapshot(delete_existing=True, expiration_days=expiration_days)
            '''
            res = self.clc.v2.API.Call('POST','/v2/operations/%s/servers/createSnapshot' % (acct_alias),
                                       json.dumps({'serverIds': server_id, 'snapshotExpirationDays': expiration_days}))
            '''
        except CLCException as ex:
            self.module.fail_json(msg='Failed to create snap shot with Error : %s' %(ex))
        return res

    def clc_create_servers_snapshot(self, server_ids, expiration_days):
        try:
            servers = self._get_servers_from_clc(
            server_ids,
            'Failed to obtain server list from the CLC API')
            servers_to_change = [
                server for server in servers if len(
                    server.GetSnapshots()) == 0]
            return [server.CreateSnapshot(delete_existing=True, expiration_days=expiration_days)
                    for server in servers_to_change], servers_to_change
            '''
            res = self.clc.v2.API.Call('POST','/v2/operations/%s/servers/createSnapshot' % (acct_alias),
                                       json.dumps({'serverIds': server_id, 'snapshotExpirationDays': expiration_days}))
            '''
        except CLCException as ex:
            self.module.fail_json(msg='Failed to create snap shot with Error : %s' %(ex))

    def clc_delete_server_snapshot(self, server_id):
        '''
        deletes the existing server snapshot
        :param acct_alias: account alias for the server
        :param server_id: the target clc server id
        :return: nothing
        '''
        try:
            server = self.clc.v2.Server(server_id)
            req = server.DeleteSnapshot()
        except CLCException as ex:
            self.module.fail_json(msg='Failed to delete snap shot for server %s. Error : %s' %(server_id,ex))
        return req

    def clc_delete_servers_snapshot(self, server_ids):
        '''
        deletes the existing servers snapshot
        :param server_ids: the list of target clc server ids
        :return: nothing
        '''
        servers = self._get_servers_from_clc(
            server_ids,
            'Failed to obtain server list from the CLC API')
        servers_to_change = [
            server for server in servers if len(
                server.GetSnapshots()) == 1]
        return [server.DeleteSnapshot()
                for server in servers_to_change], servers_to_change

    def clc_restore_servers_snapshot(self, server_ids):
        '''
        restores to the existing snapshot (if available)
        :param server_ids: the list of target clc server ids
        :return: nothing
        '''
        servers = self._get_servers_from_clc(
            server_ids,
            'Failed to obtain server list from the CLC API')
        servers_to_change = [
            server for server in servers if len(
                server.GetSnapshots()) == 1]
        return [server.RestoreSnapshot()
                for server in servers_to_change], servers_to_change

    def clc_ensure_snapshot(self, acct_alias, server_list, expiration_days, state, wait):
        """
        Create a snapshot for the given list of servers
        :param server_list: The target list of servers where the packages needs to be installed
        :param expiration_days: the number of days to keep the snapshot
        :param True/False indicating weather to wait until the snapshot action is finished
        :return: the result of snapshot job
        """

        requests = []
        command_list = []
        #servers = self._get_servers_from_clc(server_list, 'Failed to get servers from CLC')
        servers = self.clc.v2.Servers(server_list).Servers()
        try:
            for server in servers:
                if state == 'present':
                    request = self.clc_create_server_snapshot(acct_alias, server.id, expiration_days)
                    requests.append(request)
                if state == 'absent':
                    request = self.clc_delete_server_snapshot(server.id)
                    requests.append(request)
                else:
                    return self.module.fail_json(msg="Unknown State: " + state)
            if wait:
                sum(requests).WaitUntilFinished()
        except CLCException as ex:
            self.module.fail_json(msg='Failed to create snap shot with Error : %s' %(ex))
        return requests


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