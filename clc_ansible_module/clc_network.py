#!/usr/bin/env python

# CenturyLink Cloud Ansible Modules.
#
# These Ansible modules enable the CenturyLink Cloud v2 API to be called
# from an within Ansible Playbook.
#
# This file is part of CenturyLink Cloud
#
# Copyright 2016 CenturyLink
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
# CenturyLink Cloud: http://www.ctl.op
# API Documentation: https://www.ctl.io/api-docs/v2/

DOCUMENTATION = '''
module: clc_network
short_description: Create or Delete networks at CenturyLink Cloud.
description:
  - An Ansible module to Create or Delete networks at CenturyLink Cloud.
version_added: "2.0"
options:
  description:
    description:
      - A free text field for describing the network's purpose
    required: False
  id:
    description:
      - The id for the network being updated or deleted; required when state = 'absent'.
        This can be the network's id, name, or vlan -- as these can all be used to uniquely id the network.
    required: False
  location:
    description:
      - Datacenter in which the network lives/should live.
    required: True
  name:
    description:
      - The name of the network.  Used to find an existing network when state='present'.
    required: False
  state:
    description:
      - Whether to claim or release the network.
    required: False
    default: present
    choices: ['present','absent']
  wait:
    description:
      - Whether to wait for the tasks to finish before returning.
        This doesn't work when state 'present' with a name as the name is being set after the network being created.
    default: True
    required: False
    choices: [True, False]
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

---
- name: Create Network
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create and update a new network
      clc_network:
        location: 'ut1'
        state: present
        name: 'ProdNet5000'
        description: 'Production Minecraft'
      register: net

    - debug: var=net

---
- name: Delete Network
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Delete a CLC network based on id
      clc_network:
        location: 'ut1'
        state: absent
        id: 'vlan_1306_10.81.206'
      register: net

    - debug: var=net
'''

RETURN = '''
changed:
    description: A flag indicating if any change was made or not
    returned: success
    type: boolean
    sample: True
network:
    description: The network information
    returned: success
    type: dict
    sample:
        {
            "cidr": "10.101.216.0/24",
            "description": "The testing place",
            "gateway": "10.101.216.1",
            "id": "7c5fc52fd9dd48d5a6ab879bf6ab3db9",
            "links": [
                {
                    "href": "/v2-experimental/networks/wftc/ca3/7c5fc52fd9dd48d5a6ab879bf6ab3db9",
                    "rel": "self",
                    "verbs": [
                        "GET",
                        "PUT"
                    ]
                },
                {
                    "href": "/v2-experimental/networks/wftc/ca3/7c5fc52fd9dd48d5a6ab879bf6ab3db9/ipAddresses",
                    "rel": "ipAddresses",
                    "verbs": [
                        "GET"
                    ]
                },
                {
                    "href": "/v2-experimental/networks/wftc/ca3/7c5fc52fd9dd48d5a6ab879bf6ab3db9/release",
                    "rel": "release",
                    "verbs": [
                        "POST"
                    ]
                }
            ],
            "name": "test9001",
            "netmask": "255.255.255.0",
            "type": "private",
            "vlan": 716
        }
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


class ClcNetwork(object):

    clc = clc_sdk
    module = None

    def __init__(self, module):
        """
        Construct module
        """
        self.module = module
        self.network_dict = {}
        self.networks = None

        if not CLC_FOUND:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')
        if not REQUESTS_FOUND:
            self.module.fail_json(
                msg='requests library is required for this module')
        if requests.__version__ and LooseVersion(
                requests.__version__) < LooseVersion('2.5.0'):
            self.module.fail_json(
                msg='requests library  version should be >= 2.5.0')

        self._set_user_agent(self.clc)

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            id=dict(required=False),
            name=dict(required=False),
            location=dict(required=True),
            description=dict(required=False),
            wait=dict(default=True, type='bool'),
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

    # Module Behavior Goodness
    def process_request(self):
        """
        Process the request - Main Code Path
        :return: Returns with either an exit_json or fail_json
        """
        network = None
        p = self.module.params

        self._set_clc_credentials_from_env()

        self.networks = self._populate_networks(p.get('location'))

        if p.get('state') == 'absent':
            changed = self._ensure_network_absent(p)
        else:
            changed, network = self._ensure_network_present(p)

        if hasattr(network, 'data'):
            network = network.data
        elif hasattr(network, 'requests'):
            network = {
                "id": network.requests[0].id,
                "uri": network.requests[0].uri
            }

        self.module.exit_json(changed=changed, network=network)

    def _populate_networks(self, location):
        return self.clc.v2.Networks(location=location)

    @staticmethod
    def _set_user_agent(clc):
        if hasattr(clc, 'SetRequestsSession'):
            agent_string = "ClcAnsibleModule/" + __version__
            ses = requests.Session()
            ses.headers.update({"Api-Client": agent_string})
            ses.headers['User-Agent'] += " " + agent_string
            clc.SetRequestsSession(ses)

    def _ensure_network_absent(self, params):
        changed = False
        location = params.get('location')

        network = self.networks.Get(params.get('id'))

        if network is not None:
            if not self.module.check_mode:
                network.Delete(location=location)
            changed = True

        return changed

    def _ensure_network_present(self, params):
        search_key = params.get('id', None) or params.get('name', None)
        network = self.networks.Get(search_key)

        if network is None:
            changed = True
            if not self.module.check_mode:
                network = self._create_network(params)
        else:
            changed, network = self._update_network(network, params)

        return changed, network

    def _create_network(self, params):
        name = params.get('name', None)
        desc = params.get('description', None)
        request = self.clc.v2.Network.Create(location=params.get('location'))

        if params.get('wait', True):
            uri = request.requests[0].uri
            if request.WaitUntilComplete() > 0:
                self.module.fail_json(msg="Unable to create network")
            network_payload = self.clc.v2.API.Call('GET',
                                                   self.clc.v2.API.Call('GET', uri)['summary']['links'][0]['href'])
            request = self.clc.v2.Network(
                network_payload['id'], network_obj=network_payload)

            if name is not None or desc is not None:
                ignored, request = self._update_network(request, params)

        return request

    def _update_network(self, network, params):
        changed = False
        location = params.get('location')
        name = params.get('name', None)
        desc = params.get('description', None)

        if (name is not None and network.name != name) or (
                desc is not None and network.description != desc):
            changed = True
            if not self.module.check_mode:
                update_name = name if name is not None else network.name
                if desc is not None:
                    network.Update(
                        update_name,
                        description=desc,
                        location=location)
                else:
                    network.Update(update_name, location=location)

        return changed, network


def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
        argument_spec=ClcNetwork._define_module_argument_spec(),
        supports_check_mode=True)
    clc_network = ClcNetwork(module)
    clc_network.process_request()


from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
