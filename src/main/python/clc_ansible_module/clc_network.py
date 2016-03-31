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
  name:
    description:
      - The name of the network.
    required: True
  location:
    description:
      - Datacenter in which the network lives/should live.
    required: True
  description:
    description:
      - A free text field for describing the network's purpose
    required: False
  state:
    description:
      - Whether to create or delete the network.
    required: False
    default: present
    choices: ['present','absent']
  wait:
    description:
      - Whether to wait for the tasks to finish before returning.
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
    - name: Create a network
      clc_network:
        name: 'Storage Network'
        location: 'UK3'
        state: present
      register: network

    - name: debug
      debug: var=network

---
- name: Delete Network
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Delete an network
      clc_network:
        name: 'Storage Network'
        location: 'UK3'
        state: absent
      register: network

    - name: debug
      debug: var=network
'''

RETURN = '''
TBD
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


class ClcNetwork:

    clc = clc_sdk
    module = None

    def __init__(self, module):
        """
        Construct module
        """
        self.module = module
        self.network_dict = {}

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

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            name=dict(required=True),
            location=dict(required=True),
            description=dict(required=False),
            wait=dict(default=True),
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
        changed = False
        p = self.module.params

        self._set_clc_credentials_from_env()

        self.networks = self._populate_networks(p.get('location'))

        changed = self._ensure_network_present(p)

        self.module.exit_json(changed=changed)

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

    def _ensure_network_present(self, params):
      changed = False
      if self.networks.Get(params.get('name')) is None:
        changed = True
        request = self.clc.v2.Network.Create(location=params.get('location'))

        if params.get('wait') if 'wait' in params else True:
          request.WaitUntilComplete()

      return changed

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
