#!/usr/bin/python
DOCUMENTATION = '''
module: clc_modify_server
short_desciption: modify servers in CenturyLink Cloud.
description:
  - An Ansible module to modify servers in CenturyLink Cloud.
options:
  server_ids:
    description:
      - A list of server Ids to modify.
    default: []
    required: True
    aliases: []
  cpu:
    description:
      - How many CPUs to update on the server
    default: None
    required: False
    aliases: []
  memory:
    description:
      - Memory in GB.
    default: 1
    required: False
    aliases: []
  state:
    description:
      - The state to insure that the provided resources are in.
    default: 'update'
    required: False
    choices: ['update']
    aliases: []
  wait:
    description:
      - Whether to wait for the provisioning tasks to finish before returning.
    default: True
    required: False
    choices: [ True, False]
    aliases: []
'''

EXAMPLES = '''
# Note - You must set the CLC_V2_API_USERNAME And CLC_V2_API_PASSWD Environment variables before running these examples

- name: set the cpu count to 4 on a server
  clc_server:
    server_ids: ['UC1ACCTTEST01']
    cpu: 4
    state: update

- name: set the memory to 8GB on a server
  clc_server:
    server_ids: ['UC1ACCTTEST01']
    memory: 8
    state: update

- name: set the memory to 16GB and cpu to 8 core on a lust if servers
  clc_server:
    server_ids: ['UC1ACCTTEST01','UC1ACCTTEST02']
    cpu: 8
    memory: 16
    state: update
'''

import sys
import os
import datetime
import json
import socket
from time import sleep

#
#  Requires the clc-python-sdk.
#  sudo pip install clc-sdk
#
try:
    import clc as clc_sdk
    from clc import CLCException
    from clc import APIFailedResponse
except ImportError:
    CLC_FOUND = False
    clc_sdk = None
else:
    CLC_FOUND = True

class ClcModifyServer():
    clc = clc_sdk

    STATSD_HOST = '64.94.114.218'
    STATSD_PORT = 2003
    STATS_SERVER_MODIFY = 'stats_counts.wfaas.clc.ansible.server.modify'
    SOCKET_CONNECTION_TIMEOUT = 3

    def __init__(self, module):
        """
        Construct module
        """
        self.clc = clc_sdk
        self.module = module
        self.group_dict = {}

        if not CLC_FOUND:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')

    def process_request(self):
        """
        Process the request - Main Code Path
        :return: Returns with either an exit_json or fail_json
        """
        self._set_clc_credentials_from_env()

        self.module.params = ClcModifyServer._validate_module_params(self.clc,
                                                               self.module)
        p = self.module.params
        state = p.get('state')

        #
        #  Handle each state
        #

        if state == 'update':
            server_ids = p['server_ids']
            cpu = p['cpu']
            memory = p['memory']
            if not isinstance(server_ids, list):
                return self.module.fail_json(
                    msg='server_ids needs to be a list of instances to modify: %s' %
                    server_ids)

            (changed,
             server_dict_array,
             new_server_ids) = ClcModifyServer._modify_servers(module=self.module,
                                                         clc=self.clc,
                                                         server_ids=server_ids)

        self.module.exit_json(
            changed=changed,
            server_ids=new_server_ids,
            servers=server_dict_array)

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            server_ids=dict(type='list'),
            state=dict(default='update', choices=['update']),
            cpu=dict(),
            memory=dict(),
            wait=dict(type='bool', default=True)
        )
        return argument_spec

    def _set_clc_credentials_from_env(self):
        """
        Set the CLC Credentials on the sdk by reading environment variables
        :return: none
        """
        env = os.environ
        v2_api_token = env.get('Authorization', False)
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

    @staticmethod
    def _validate_module_params(clc, module):
        """
        Validate the module params, and lookup default values.
        :param clc: clc-sdk instance to use
        :param module: module to validate
        :return: dictionary of validated params
        """
        params = module.params

        params['cpu']            = ClcModifyServer._find_cpu(clc, module)
        params['memory']         = ClcModifyServer._find_memory(clc, module)

        return params

    @staticmethod
    def _find_cpu(clc, module):
        """
        Find or validate the CPU value by calling the CLC API
        :param clc: clc-sdk instance to use
        :param module: module to validate
        :return: Int value for CPU
        """
        cpu = module.params.get('cpu')
        state = module.params.get('state')

        if not cpu and state == 'update':
            module.fail_json(msg=str("Cannot determine a default cpu value. Please provide a value for cpu."))
        return cpu

    @staticmethod
    def _find_memory(clc, module):
        """
        Find or validate the Memory value by calling the CLC API
        :param clc: clc-sdk instance to use
        :param module: module to validate
        :return: Int value for Memory
        """
        memory = module.params.get('memory')
        state = module.params.get('state')

        if not memory and state == 'update':
            module.fail_json(msg=str("Cannot determine a default memory value. Please provide a value for memory."))
        return memory

    @staticmethod
    def _wait_for_requests(clc, requests, servers, wait):
        """
        Block until server provisioning requests are completed.
        :param clc: the clc-sdk instance to use
        :param requests: a list of clc-sdk.Request instances
        :param servers: a list of servers to refresh
        :param wait: a boolean on whether to block or not.  This function is skipped if True
        :return: none
        """
        if wait:
            # Requests.WaitUntilComplete() returns the count of failed requests
            failed_requests_count = sum([request.WaitUntilComplete() for request in requests])

            if failed_requests_count > 0:
                raise clc
            else:
                ClcModifyServer._refresh_servers(servers)


    @staticmethod
    def _refresh_servers(servers):
        """
        Loop through a list of servers and refresh them
        :param servers: list of clc-sdk.Server instances to refresh
        :return: none
        """
        for server in servers:
            server.Refresh()

    @staticmethod
    def _modify_servers(module, clc, server_ids):
        """
        modify the servers configuration on the provided list
        :param module: the AnsibleModule object
        :param clc: the clc-sdk instance to use
        :param server_ids: list of servers to modify
        :return: a list of dictionaries with server information about the servers that were started or stopped
        """
        p = module.params
        wait = p.get('wait')
        cpu = p.get('cpu')
        memory = p.get('memory')
        changed = False
        changed_servers = []
        server_dict_array = []
        result_server_ids = []
        requests = []

        if not isinstance(server_ids, list) or len(server_ids) < 1:
            return module.fail_json(
                msg='server_ids should be a list of servers, aborting')

        servers = clc.v2.Servers(server_ids).Servers()
        for server in servers:
            if not cpu:
                cpu = server.cpu
            if not memory:
                memory = server.memory
            if memory != server.memory or cpu != server.cpu:
                changed_servers.append(server)
                requests.append(ClcModifyServer._modify_clc_server(clc, module, None, server.id, cpu, memory))
                changed = True

        if wait:
            for r in requests:
                r.WaitUntilComplete()
            for server in changed_servers:
                server.Refresh()

        for server in changed_servers:
            server_dict_array.append(server.data)
            result_server_ids.append(server.id)

        return changed, server_dict_array, result_server_ids

    @staticmethod
    def _modify_clc_server(clc, module, acct_alias, server_id, cpu, memory):
        """
        Modify the memory or CPU on a clc server.  This function is not yet implemented.
        :param clc: the clc-sdk instance to use
        :param acct_alias: the clc account alias to look up the server
        :param server_id: id of the server to modify
        :param cpu: the new cpu value
        :param memory: the new memory value
        :return: clc-sdk.Request instance pointing to the queued provisioning request
        """
        if not acct_alias:
            acct_alias = clc.v2.Account.GetAlias()
        if not server_id:
            return module.fail_json(msg='server_id must be provided to modify the server')

        # Fetch the existing server information
        server = clc.v2.Server(server_id)
        job_obj = clc.v2.API.Call('PATCH',
                                  'servers/%s/%s' % (acct_alias,
                                                     server_id),
                                  json.dumps([{"op": "set",
                                               "member": "memory",
                                               "value": memory},
                                              {"op": "set",
                                               "member": "cpu",
                                               "value": cpu}]))
        result = clc.v2.Requests(job_obj)
        # Push the server modify count metric to statsd
        ClcModifyServer._push_metric(ClcModifyServer.STATS_SERVER_MODIFY, 1)
        return result

    @staticmethod
    def _push_metric(path, count):
        try:
            sock = socket.socket()
            sock.settimeout(ClcModifyServer.SOCKET_CONNECTION_TIMEOUT)
            sock.connect((ClcModifyServer.STATSD_HOST, ClcModifyServer.STATSD_PORT))
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
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
            argument_spec=ClcModifyServer._define_module_argument_spec()
        )
    clc_modify_server = ClcModifyServer(module)
    clc_modify_server.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()