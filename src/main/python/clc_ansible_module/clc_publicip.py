#!/usr/bin/python

# CenturyLink Cloud Ansible Modules.
#
# These Ansible modules enable the CenturyLink Cloud v2 API to be called
# from an within Ansible Playbook.
#
# This file is part of CenturyLink Cloud, and is maintained
# by the Workflow as a Service Team
#
# Copyright 2015 CenturyLink Cloud
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
module: clc_publicip
short_description: Add and Delete public ips on servers in CenturyLink Cloud.
description:
  - An Ansible module to add or delete public ip addresses on an existing server or servers in CenturyLink Cloud.
options:
  protocol:
    descirption:
      - The protocol that the public IP will listen for.
    default: TCP
    required: False
  ports:
    description:
      - A list of ports to expose.
    required: True
  server_ids:
    description:
      - A list of servers to create public ips on.
    required: True
  state:
    description:
      - Determine wheteher to create or delete public IPs. If present module will not create a second public ip if one
        already exists.
    default: present
    choices: ['present', 'absent']
    required: False
  wait:
    description:
      - Whether to wait for the tasks to finish before returning.
    choices: [ True, False ]
    default: True
    required: False
'''

EXAMPLES = '''
# Note - You must set the CLC_V2_API_USERNAME And CLC_V2_API_PASSWD Environment variables before running these examples

- name: Add Public IP to Server
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create Public IP For Servers
      clc_publicip:
        protocol: 'TCP'
        ports:
            - 80
        server_ids:
            - UC1ACCTSRVR01
            - UC1ACCTSRVR02
        state: present
      register: clc

    - name: debug
      debug: var=clc

- name: Delete Public IP from Server
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create Public IP For Servers
      clc_publicip:
        server_ids:
            - UC1ACCTSRVR01
            - UC1ACCTSRVR02
        state: absent
      register: clc

    - name: debug
      debug: var=clc
'''
import socket
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


class ClcPublicIp(object):
    clc = clc_sdk
    module = None
    group_dict = {}

    STATSD_HOST = '64.94.114.218'
    STATSD_PORT = 2003
    STATS_PUBLICIP_CREATE = 'stats_counts.wfaas.clc.ansible.publicip.create'
    STATS_PUBLICIP_DELETE = 'stats_counts.wfaas.clc.ansible.publicip.delete'
    SOCKET_CONNECTION_TIMEOUT = 3

    def __init__(self, module):
        """
        Construct module
        """
        self.module = module
        if not CLC_FOUND:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')

    def process_request(self, params):
        """
        Process the request - Main Code Path
        :param params: dictionary of module parameters
        :return: Returns with either an exit_json or fail_json
        """
        self._set_clc_credentials_from_env()
        server_ids = params['server_ids']
        ports = params['ports']
        protocol = params['protocol']
        state = params['state']
        wait = params['wait']
        command_list = []

        if state == 'present':
            if not self.module.check_mode:
                command_list.append(
                    lambda: self.ip_create_command(
                        server_ids=server_ids,
                        protocol=protocol,
                        ports=ports))
        elif state == 'absent':
            if not self.module.check_mode:
                command_list.append(
                    lambda: self.ip_delete_command(
                        server_ids=server_ids))
        else:
            return self.module.fail_json(msg="Unknown State: " + state)

        has_made_changes, result_servers, result_server_ids = self.run_clc_commands(
            command_list)
        return self.module.exit_json(
            changed=has_made_changes,
            servers=result_servers,
            server_ids=result_server_ids)

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            server_ids=dict(type='list', required=True),
            protocol=dict(default='TCP'),
            ports=dict(type='list'),
            wait=dict(type='bool', default=True),
            state=dict(default='present', choices=['present', 'absent']),
        )
        return argument_spec

    def _set_clc_credentials_from_env(self):
        """
        Set the CLC Credentials on the sdk by reading environment variables
        :return: none
        """
        env = os.environ
        v2_api_token = env.get('CLC_V2_API_TOKEN', False)
        v2_api_username = env.get('CLC_V2_API_USERNAME', False)
        v2_api_passwd = env.get('CLC_V2_API_PASSWD', False)
        clc_alias = env.get('CLC_ACCT_ALIAS', False)
        api_url = env.get('CLC_V2_API_URL', False)

        if api_url:
            self.clc.defaults.ENDPOINT_URL_V2 = api_url

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

    def run_clc_commands(self, command_list):
        """
        Executes the CLC commands
        :param command_list: list of commands to run
        :return: (has_made_changes, result_changed_servers, changed_server_ids)
            has_made_changes: Boolean on whether a change was made
            result_changed_servers: The result from the CLC API call
            changed_server_ids: A list of the changed servers
        """
        requests_list = []
        changed_servers = []
        for command in command_list:
            requests, servers = command()
            requests_list += requests
            changed_servers += servers
        wait = self.module.params.get('wait')
        self._wait_for_requests_to_complete(requests_list, wait)
        changed_server_ids, changed_servers = self._refresh_server_public_ips(
            changed_servers)
        has_made_changes, result_changed_servers = self._parse_server_results(
            changed_servers)
        return has_made_changes, result_changed_servers, changed_server_ids

    def ip_create_command(self, server_ids, protocol, ports):
        """
        Creates public ip
        :param server_ids: list of server ids to change
        :param protocol:  The protocol the public IP will listen for
        :param ports: List of ports to expose
        :return: returns servers that IPs were created on
        """
        servers = self._get_servers_from_clc_api(
            server_ids,
            'Failed to obtain server list from the CLC API')
        servers_to_change = [
            server for server in servers if len(
                server.PublicIPs().public_ips) == 0]
        ports_to_expose = [{'protocol': protocol, 'port': port}
                           for port in ports]
        ClcPublicIp._push_metric(
            ClcPublicIp.STATS_PUBLICIP_CREATE,
            len(servers_to_change))

        result = [server.PublicIPs().Add(ports_to_expose)
                  for server in servers_to_change], servers_to_change
        return result

    def ip_delete_command(self, server_ids):
        """
        Deletes public ip
        :param server_ids: list of servers to delete public ips from
        :return: returns servers that IPs were deleted from
        """
        servers = self._get_servers_from_clc_api(
            server_ids,
            'Failed to obtain server list from the CLC API')
        servers_to_change = [
            server for server in servers if len(
                server.PublicIPs().public_ips) > 0]

        ips_to_delete = []
        for server in servers_to_change:
            for ip_address in server.PublicIPs().public_ips:
                ips_to_delete.append(ip_address)
        ClcPublicIp._push_metric(
            ClcPublicIp.STATS_PUBLICIP_DELETE,
            len(servers_to_change))

        result = [ip.Delete() for ip in ips_to_delete], servers_to_change
        return result

    def _wait_for_requests_to_complete(self, requests_lst, wait='True', action='create'):
        """
        Waits for the requests to complete
        :param requests_lst: a list of the requests that a being waited on
        :param action: action that is waiting to complete
        :return: none
        """
        if wait != True:
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

    def _refresh_server_public_ips(self, servers_to_refresh):
        """
        Refresh the public ip server list
        :param servers_to_refresh: list of servers to refresh
        :return: (refreshed_server_ids, refreshed_servers)
            refreshed_server_ids: whether the ids were refreshed or not
            refreshed_servers: list of servers that were refreshed
        """
        refreshed_server_ids = [server.id for server in servers_to_refresh]
        refreshed_servers = self._get_servers_from_clc_api(
            refreshed_server_ids,
            'Failed to refresh server list from CLC API')
        return refreshed_server_ids, refreshed_servers

    @staticmethod
    def _parse_server_results(servers):
        """
        Parses servers results for IP information
        :param servers: list of servers
        :return: (changed, servers_result)
            changed: returns a Boolean if public Ip was added
            servers_result: returns ip data of the servers
        """
        servers_result = []
        changed = False
        for server in servers:
            has_publicip = len(server.PublicIPs().public_ips) > 0
            if has_publicip:
                changed = True
                public_ip = str(server.PublicIPs().public_ips[0].id)
                internal_ip = str(server.PublicIPs().public_ips[0].internal)
                server.data['public_ip'] = public_ip
                server.data['internal_ip'] = internal_ip
            ipaddress = server.data['details']['ipAddresses'][0]['internal']
            server.data['ipaddress'] = ipaddress
            servers_result.append(server.data)
        return changed, servers_result

    def _get_servers_from_clc_api(self, server_ids, message):
        """
        Gets list of servers form CLC api
        """
        try:
            return self.clc.v2.Servers(server_ids).servers
        except CLCException as exception:
            self.module.fail_json(msg=message + ': %s' % exception)

    @staticmethod
    def _push_metric(path, count):
        """
        Pushes out metrics of when module is run
        """
        try:
            sock = socket.socket()
            sock.settimeout(ClcPublicIp.SOCKET_CONNECTION_TIMEOUT)
            sock.connect((ClcPublicIp.STATSD_HOST, ClcPublicIp.STATSD_PORT))
            sock.sendall('%s %s %d\n' % (path, count, int(time.time())))
            sock.close()
        except socket.gaierror:
            # do nothing, ignore and move forward
            error = ''
        except socket.error:
            # nothing, ignore and move forward
            error = ''


def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
        argument_spec=ClcPublicIp._define_module_argument_spec(),
        supports_check_mode=True
    )
    clc_public_ip = ClcPublicIp(module)
    clc_public_ip.process_request(module.params)

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
