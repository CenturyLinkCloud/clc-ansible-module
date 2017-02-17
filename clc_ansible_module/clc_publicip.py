#!/usr/bin/python

# CenturyLink Cloud Ansible Modules.
#
# These Ansible modules enable the CenturyLink Cloud v2 API to be called
# from an within Ansible Playbook.
#
# This file is part of CenturyLink Cloud, and is maintained
# by the Workflow as a Service Team
#
# Copyright 2015 CenturyLink 
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

DOCUMENTATION = '''
module: clc_publicip
short_description: Add and Delete public ips on servers in CenturyLink Cloud.
description:
  - An Ansible module to add or delete public ip addresses on an existing server or servers in CenturyLink Cloud.
version_added: "2.0"
options:
  protocol:
    description:
      - The protocol that the public IP will listen for. This is required when state is 'present'
    default: TCP
    choices: ['TCP', 'UDP', 'ICMP']
    required: False
  ports:
    description:
      - A list of ports to expose. This is required when state is 'present'
    required: False
    default: None
  server_ids:
    description:
      - A list of servers to create public ips on.
        Required if server_id is not passed as a parameter
    required: False
  server_id:
    description:
      - ID of the server on which to create public ips.
        Required if server_ids is not passed as a parameter
    required: False
  internal_ip:
    description:
      - Internal IP to NAT the public IP address.
        Must already exist on the server.
    required: False
  source_restrictions:
    description:
      - The source IP address range allowed to access the new public IP address.
        Used to restrict access to only the specified range of source IPs.
        The IP range allowed to access the public IP should be specified using CIDR notation.
    required: False
    default: None
  state:
    description:
      - Determine whether to create or delete public IPs. If present module will not create a second public ip if one
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
requirements:
    - python = 2.7
author: "CLC Runner (@clc-runner)"
notes:
    - To use this module, it is required to set the below environment variables which enables access to the
      Centurylink Cloud
          - CLC_V2_API_USERNAME, the account login id for the centurylink cloud
          - CLC_V2_API_PASSWORD, the account password for the centurylink cloud
    - Alternatively, the module accepts the API token and account alias. The API token can be generated using the
      CLC account login and password via the HTTP api call @ https://api.ctl.io/v2/authentication/login
          - CLC_V2_API_TOKEN, the API token generated from https://api.ctl.io/v2/authentication/login
          - CLC_ACCT_ALIAS, the account alias associated with the centurylink cloud
    - Users can set CLC_V2_API_URL to specify an endpoint for pointing to a different CLC environment.
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
            - UC1TEST-SVR01
            - UC1TEST-SVR02
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
            - UC1TEST-SVR01
            - UC1TEST-SVR02
        state: absent
      register: clc

    - name: debug
      debug: var=clc
'''

RETURN = '''
changed:
    description: A flag indicating if any change was made or not
    returned: success
    type: boolean
    sample: True
server_ids:
    description: The list of server ids that are changed
    returned: success
    type: list
    sample:
        [
            "UC1TEST-SVR01",
            "UC1TEST-SVR02"
        ]
'''

__version__ = '${version}'

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException


class ClcPublicIp(object):

    def __init__(self, module):
        """
        Construct module
        """
        self.clc_auth = {}
        self.module = module

    def process_request(self):
        """
        Process the request - Main Code Path
        :return: Returns with either an exit_json or fail_json
        """
        self.clc_auth = clc_common.authenticate(self.module)

        state = self.module.params['state']

        if state == 'absent':
            changed, changed_ids, requests = self.ensure_public_ip_absent()
        else:
            changed, changed_ids, requests = self.ensure_public_ip_present()
        self._wait_for_requests_to_complete(requests)

        return self.module.exit_json(changed=changed,
                                     server_ids=changed_ids)

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            server_ids=dict(type='list', required=False),
            server_id=dict(type='str', default=None, required=False),
            internal_ip=dict(type='str', default=None, required=False),
            protocol=dict(type='str', default='TCP',
                          choices=['TCP', 'UDP', 'ICMP']),
            ports=dict(type='list'),
            source_restrictions=dict(type='list'),
            wait=dict(type='bool', default=True),
            state=dict(type='str', default='present',
                       choices=['present', 'absent']),
        )
        mutually_exclusive = [
            ['server_ids', 'server_id'],
            ['server_ids', 'internal_ip']
        ]
        return {'argument_spec': argument_spec,
                'mutually_exclusive': mutually_exclusive}

    def ensure_public_ip_present(self):
        """
        Ensures the given server ids having the public ip available
        :return: (changed, changed_server_ids, results)
                  changed: A flag indicating if there is any change
                  changed_server_ids : the list of server ids that are changed
                  results: The result list from clc public ip call
        """
        p = self.module.params
        server_ids = p.get('server_ids')
        server_id = p.get('server_id')
        protocol = p.get('protocol')
        ports = p.get('ports')
        internal_ip = p.get('internal_ip')
        source_restrictions = p.get('source_restrictions')

        if not server_ids and not server_id:
            return self.module.fail_json(
                msg='Must specify either server_id or server_ids.')
        if not protocol or not ports:
            return self.module.fail_json(
                msg='Must specify protocol and ports when state is present.')

        if not server_ids:
            server_ids = [server_id]

        changed = False
        results = []
        changed_server_ids = []
        restrictions_list = []

        servers = clc_common.servers_by_id(
            self.module, self.clc_auth, server_ids)
        servers = [clc_common.server_ip_addresses(self.module, self.clc_auth, s)
                   for s in servers]

        ports_to_expose = [{'protocol': protocol, 'port': int(port)}
                           for port in ports]
        ports_to_expose.append({'protocol': 'ICMP', 'port': 0})
        if source_restrictions:
            restrictions_list = [{'cidr': cidr} for cidr in source_restrictions]

        for server in servers:
            if not self.module.check_mode:
                public_ip = None
                if internal_ip:
                    ips = [i for i in server.data['details']['ipAddresses']]
                    if internal_ip not in [i['internal'] for i in ips]:
                        return self.module.fail_json(
                            msg='Internal IP address: {ip} is not present on '
                                'server: {id}.'.format(ip=internal_ip,
                                                       id=server.id))
                    else:
                        ip = [i for i in ips if i['internal'] == internal_ip][0]
                        if 'public' in ip:
                            public_ip = ip['public']
                else:
                    if 'publicip' in server.data:
                        public_ip = server.data['publicip']
                if public_ip:
                    update_required = self._update_publicip_required(
                        server, public_ip,
                        ports_to_expose, restrictions_list)
                    if not update_required:
                        continue
                    result = self._update_publicip(
                        server, public_ip,
                        ports_to_expose, source_restrictions=restrictions_list)
                else:
                    result = self._add_publicip(
                        server,
                        ports_to_expose, source_restrictions=restrictions_list)
                results.append(result)
            changed_server_ids.append(server.id)
            changed = True
        return changed, changed_server_ids, results

    def _add_publicip(self, server, ports_to_expose, source_restrictions=None):
        internal_ip = self.module.params.get('internal_ip')
        if not internal_ip:
            internal_ip = server.data['details']['ipAddresses'][0]['internal']
        payload = {'ports': ports_to_expose,
                   'internalIPAddress': internal_ip}
        if source_restrictions:
            payload['sourceRestrictions'] = source_restrictions
        try:
            result = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'POST',
                '/servers/{alias}/{id}/publicIPAddresses'.format(
                    alias=self.clc_auth['clc_alias'], id=server.id),
                data=payload)
        except ClcApiException as ex:
            return self.module.fail_json(
                msg='Failed to add public ip to the server: {id}. '
                    '{msg}'.format(id=server.id, msg=ex.message))
        return result

    def _update_publicip_required(self, server, ip_address,
                                  ports_to_expose, source_restrictions):
        try:
            result = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'GET',
                '/servers/{alias}/{id}/publicIPAddresses/{ip}'.format(
                    alias=self.clc_auth['clc_alias'], id=server.id,
                    ip=ip_address),
                timeout=60)
        except ClcApiException as ex:
            return self.module.fail_json(
                msg='Failed to get public ip: {ip} on the server: {id}. '
                    '{msg}'.format(ip=ip_address, id=server.id,
                                   msg=ex.message))
        if source_restrictions != result['sourceRestrictions']:
            return True
        if ports_to_expose != result['ports']:
            return True
        return False

    def _update_publicip(self, server, ip_address, ports_to_expose,
                         source_restrictions=None):
        payload = {'ports': ports_to_expose}
        if source_restrictions:
            payload['sourceRestrictions'] = source_restrictions
        try:
            result = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'PUT',
                '/servers/{alias}/{id}/publicIPAddresses/{ip}'.format(
                    alias=self.clc_auth['clc_alias'], id=server.id,
                    ip=ip_address),
                data=payload)
        except ClcApiException as ex:
            return self.module.fail_json(
                msg='Failed to update public ip: {ip} on the server: {id}. '
                    '{msg}'.format(ip=ip_address, id=server.id,
                                   msg=ex.message))
        return result

    def ensure_public_ip_absent(self):
        """
        Ensures the given server ids having the public ip removed if there is any
        :return: (changed, changed_server_ids, results)
                  changed: A flag indicating if there is any change
                  changed_server_ids : the list of server ids that are changed
                  results: The result list from clc public ip call
        """
        server_ids = self.module.params.get('server_ids')
        server_id = self.module.params.get('server_id')
        internal_ip = self.module.params.get('internal_ip')
        if not server_ids and not server_id:
            return self.module.fail_json(
                msg='Must specify either server_id or server_ids.')

        if not server_ids:
            server_ids = [server_id]

        changed = False
        results = []
        changed_server_ids = []
        servers = clc_common.servers_by_id(self.module, self.clc_auth,
                                           server_ids)

        servers = [clc_common.server_ip_addresses(self.module, self.clc_auth, s)
                   for s in servers]
        for server in servers:
            if 'publicip' in server.data:
                if internal_ip:
                    internal_ips = [i['internal'] for i
                                    in server.data['details']['ipAddresses']]
                    if internal_ip not in internal_ips:
                        self.module.fail_json(
                            msg='Internal IP address: {ip} is not present on '
                                'server: {id}'.format(ip=internal_ip,
                                                      id=server.id))
                if not self.module.check_mode:
                    results.extend(self._remove_publicip_addresses(server))
                changed_server_ids.append(server.id)
                changed = True
        return changed, changed_server_ids, results

    def _remove_publicip_addresses(self, server):
        internal_ip = self.module.params.get('internal_ip')
        results = []
        ips = [ip for ip in server.data['details']['ipAddresses']
               if 'public' in ip]
        for ip in ips:
            if internal_ip and ip['internal'] != internal_ip:
                continue
            results.append(self._delete_publicip(server, ip['public']))
        return results

    def _delete_publicip(self, server, ip_address):
        try:
            result = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'DELETE',
                '/servers/{alias}/{id}/publicIPAddresses/{ip}'.format(
                    alias=self.clc_auth['clc_alias'],
                    id=server.id, ip=ip_address))
        except ClcApiException as ex:
            return self.module.fail_json(
                msg='Failed to remove public ip from the server: {id}. '
                    '{msg}'.format(id=server.id, msg=ex.message))
        return result

    def _wait_for_requests_to_complete(self, requests_lst):
        """
        Waits until the CLC requests are complete if the wait argument is True
        :param requests_lst:  a list of CLC API JSON responses
        :return: none
        """
        wait = self.module.params.get('wait')
        if wait:
            failed_requests_count = clc_common.wait_on_completed_operations(
                self.module, self.clc_auth,
                clc_common.operation_id_list(requests_lst))

            if failed_requests_count > 0:
                self.module.fail_json(
                    msg='Unable to process public ip request')


def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    argument_dict = ClcPublicIp._define_module_argument_spec()
    module = AnsibleModule(supports_check_mode=True, **argument_dict)
    clc_public_ip = ClcPublicIp(module)
    clc_public_ip.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
