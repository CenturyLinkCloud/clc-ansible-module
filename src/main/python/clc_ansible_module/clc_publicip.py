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
  private_ip:
    description:
      - The private ip to which the public IP should be NAT'd.
        If not provided, a private ip will be provisioned on the server's
        primary network
    default: None
    choices: Any private ip belonging to the server
    required: False
  ports:
    description:
      - A list of structures specifying port (required), protocol ['TCP','UDP'] (required), and
        port_to (optional; used when specifying a range of ports)
      - Example: {protocol: 'TCP', port: 10000, port_to: 10050}
    required: False
    default: None
  server_id:
    description:
      - The server on which to create a public ip
    required: True
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
    - requests >= 2.5.0
    - clc-sdk
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
        ports:
            - {port: 80, protocol: 'TCP'}
            - {port: 10000, port_to: 10050}
            - {port: 24601, protocol: 'UDP'}
        server_id: UC1TEST-SVR01
        state: present
      register: clc

    - name: debug
      debug: var=clc

- name: Delete Public IP from Server
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Delete Public IP For Servers
      clc_publicip:
        server_id: UC1TEST-SVR01
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
server_id:
    description: The server id that is changed
    returned: success
    type: list
    sample:
        "UC1TEST-SVR01"
'''

__version__ = '${version}'

from distutils.version import LooseVersion

try:
    import requests
except ImportError:
    REQUESTS_FOUND = False
else:
    REQUESTS_FOUND = True

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

    def __init__(self, module):
        """
        Construct module
        """
        self.module = module
        if not CLC_FOUND:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')
        if not REQUESTS_FOUND:
            self.module.fail_json(
                msg='requests library is required for this module')
        if requests.__version__ and LooseVersion(requests.__version__) < LooseVersion('2.5.0'):
            self.module.fail_json(
                msg='requests library  version should be >= 2.5.0')

        self._set_user_agent(self.clc)

    def process_request(self):
        """
        Process the request - Main Code Path
        :return: Returns with either an exit_json or fail_json
        """
        self._set_clc_credentials_from_env()
        params = self.module.params

        server_id = params.get('server_id')
        private_ip = params.get('private_ip')
        ports = self._validate_ports(params.get('ports'))
        restrictions = params.get('source_restrictions')
        state = params.get('state')

        if state == 'present':
            changed, changed_server_id, request = self.ensure_public_ip_present(
                server_id=server_id,
                private_ip=private_ip,
                ports=ports,
                source_restrictions=restrictions
            )
        elif state == 'absent':
            changed, changed_server_id, request = self.ensure_public_ip_absent(
                server_id=server_id)
        else:
            return self.module.fail_json(msg="Unknown State: " + state)
        self._wait_for_request_to_complete(request)
        return self.module.exit_json(changed=changed,
                                     server_id=changed_server_id)

    def _validate_ports(self, ports):
        """
        Validates the provided list of port structures
        Note that this is required because Ansible does not seem to validate argument specs
        beyond the first level of the dictionary
        :param ports: list of dictionaries specifying port, protocol, and an optional port_to
        :return: list of validated ports
        """
        validated_ports = []

        for entry in ports:
            if 'port' not in entry and 'protocol' not in entry:
                continue
            elif 'protocol' not in entry:
                entry['protocol'] = 'TCP'
            elif entry['protocol'] not in ['TCP', 'UDP']:
                self.module.fail_json(
                    msg="Valid protocols for this module are: [TCP, UDP]: You specified '{0}'".format(entry['protocol'])
                )
            elif 'port' not in entry:
                self.module.fail_json(msg="You must provide a port")

            validated_ports.append(entry)

        return validated_ports


    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            server_id=dict(required=True),
            private_ip=dict(default=None),
            ports=dict(
                type='list',
                default=[],
                protocol=dict(default='TCP', choices=['TCP', 'UDP']),
                port=dict(required=True),
                port_to=dict()
            ),
            source_restrictions=dict(type='list'),
            wait=dict(type='bool', default=True),
            state=dict(default='present', choices=['present', 'absent']),
        )
        return argument_spec

    def ensure_public_ip_present(self, server_id, ports=[], private_ip=None, source_restrictions=None):
        """
        Ensures the given server ids having the public ip available
        :param server_id: the server id
        :param private_ip: optional private ip to which public ip should be NAT'ed
        :param ports: list of dictionaries specifying ports and protocols to expose
        :param source_restrictions: The list of IP range allowed to access the public IP, specified using CIDR notation.
        :return: (changed, changed_server_id, result)
                  changed: A flag indicating if there is any change
                  changed_server_id : the server id that is changed
                  result: The result from clc public ip call
        """
        changed = False
        result  = ""
        changed_server_id = ""
        restrictions_list = []
        server = self._get_server_from_clc(
            server_id,
            'Failed to obtain server from the CLC API')

        if source_restrictions:
            restrictions_list = [{'cidr': cidr} for cidr in source_restrictions]

        if not self.module.check_mode:
            result = self._add_publicip_to_server(server, ports, private_ip=private_ip, source_restrictions=restrictions_list)
        changed_server_id = server.id
        changed = True
        return changed, changed_server_id, result

    def _add_publicip_to_server(self, server, ports_to_expose, private_ip=None, source_restrictions=None):
        result = None

        # We are mimicing Control here and auto-enabling ping
        # Port is set to 0 because all 'ports' must have a port
        ports_to_expose.insert(0, {'protocol': 'ICMP', 'port': 0})

        try:
            result = server.PublicIPs().Add(
                ports=ports_to_expose
                , source_restrictions=source_restrictions
                , private_ip=private_ip
            )
        except CLCException, ex:
            self.module.fail_json(msg='Failed to add public ip to the server : {0}. {1}'.format(
                server.id, ex.response_text
            ))
        return result

    def ensure_public_ip_absent(self, server_id):
        """
        Ensures the given server ids having the public ip removed if there is any
        :param server_id: the server id
        :return: (changed, changed_server_id, result)
                  changed: A flag indicating if there is any change
                  changed_server_id : the changed server id
                  result: The result from clc public ip call
        """
        changed = False
        result  = ""
        changed_server_id = ""
        server  = self._get_server_from_clc(
            server_id,
            'Failed to obtain server from the CLC API')
        if not self.module.check_mode:
            result = self._remove_publicip_from_server(server)
        changed_server_id = server.id
        changed = True
        return changed, changed_server_id, result

    def _remove_publicip_from_server(self, server):
        result = None
        try:
            for ip_address in server.PublicIPs().public_ips:
                    result = ip_address.Delete()
        except CLCException, ex:
            self.module.fail_json(msg='Failed to remove public ip from the server : {0}. {1}'.format(
                server.id, ex.response_text
            ))
        return result

    def _wait_for_request_to_complete(self, request):
        """
        Waits until the CLC request is complete if the wait argument is True
        :param request: The CLC request objects
        :return: none
        """
        if not self.module.params['wait']:
            return
        request.WaitUntilComplete()
        for request_details in request.requests:
            if request_details.Status() != 'succeeded':
                self.module.fail_json(
                    msg='Unable to process public ip request')

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

    def _get_server_from_clc(self, server_id, message):
        """
        Gets list of servers form CLC api
        """
        try:
            return self.clc.v2.Server(server_id)
        except CLCException as exception:
            self.module.fail_json(msg=message + ': %s' % exception)

    @staticmethod
    def _set_user_agent(clc):
        if hasattr(clc, 'SetRequestsSession'):
            agent_string = "ClcAnsibleModule/" + __version__
            ses = requests.Session()
            ses.headers.update({"Api-Client": agent_string})
            ses.headers['User-Agent'] += " " + agent_string
            clc.SetRequestsSession(ses)


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
    clc_public_ip.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
