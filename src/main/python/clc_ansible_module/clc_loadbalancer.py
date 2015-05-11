#!/usr/bin/python
DOCUMENTATION = '''
module:
short_desciption: Create, Delete shared loadbalancers in CenturyLink Cloud.
description:
  - An Ansible module to Create, Delete shared loadbalancers in CenturyLink Cloud.
options:
  name:
    description:
    - Specify a name for the loadbalancer to be manipulated
    default: None
    required: False
    aliases: []
  location:
    description:
    - Specify a datacenter for loadbalancer
    default:
    required: False
    aliases: []
  alias:
    description:
    - Account alias for the provisioned loadbalancer
    default:
    - Default credentials for the API credentials
    required: False
    aliases: []
  description:
    description:
    - Description to set for the loadbalancer
    default: None
    required: False
    aliases: []
  state:
    description:
    - State to ensure the resources are in
    default: 'present'
    required: False
    choices: ['present', 'absent']
    aliases: []
'''

EXAMPLES = '''
# Note - You must set the CLC_V2_API_USERNAME And CLC_V2_API_PASSWD Environment variables before running these examples
- name: Delete Loadbalancer named Mustang
  clc_loadbalancer:
    name: Mustang
    alias: FMC
    location: UC1
    state: absent
- name: Create Loadbalancer named Mustang
  clc_loadbalancer:
    name: Mustang
    alias: FMC
    location: UC1
    description: Shared Loadbalancer for distributing data
    state: present
'''

import sys
import os
import datetime
import json

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


class ClcLoadBalancer():

    clc = None

    def __init__(self, module):
        """
        Construct module
        """
        self.clc = clc_sdk
        self.module = module
        self.lb_dict = {}

        if not CLC_FOUND:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')

    def process_request(self):
        """
        Execute the main code path, and handle the request
        :return: none
        """

        loadbalancer_name=self.module.params.get('name')
        loadbalancer_alias=self.module.params.get('alias')
        loadbalancer_location=self.module.params.get('location')
        loadbalancer_description=self.module.params.get('description')
        loadbalancer_status=self.module.params.get('status')
        state=self.module.params.get('state')

        self.set_clc_credentials_from_env()

        self.lb_dict = self._get_loadbalancer_list(alias=loadbalancer_alias, location=loadbalancer_location)

        if state == 'present':
            changed, result_lb = self.ensure_loadbalancer_present(name=loadbalancer_name,
                                                                  alias=loadbalancer_alias,
                                                                  location=loadbalancer_location,
                                                                  description=loadbalancer_description,
                                                                  status=loadbalancer_status)
            self.module.exit_json(changed=changed, loadbalancer=result_lb)

        elif state == 'absent':
            changed, result_lb = self.ensure_loadbalancer_absent(name=loadbalancer_name,
                                                                 alias=loadbalancer_alias,
                                                                 location=loadbalancer_location)
            self.module.exit_json(changed=changed, loadbalancer=result_lb)
    #
    #  Functions to define the Ansible module and its arguments
    #
    def ensure_loadbalancer_present(self,name,alias,location,description,status):
        """
        Check for loadbalancer presence (available)
        :param name: Name of loadbalancer
        :param alias: Alias of account
        :param location: Datacenter
        :param description: Description of loadbalancer
        :param status: Enabled / Disabled
        :return: True / False
        """
        changed = False

        lb_exists = self._loadbalancer_exists(name=name)
        if lb_exists:
            result = name
            changed = False
        else:
            result = self.create_loadbalancer(name=name,
                                          alias=alias,
                                          location=location,
                                          description=description,
                                          status=status)
            changed = True

        return changed, result

    def ensure_loadbalancer_absent(self,name,alias,location):
        """
        Check for loadbalancer presence (not available)
        :param name: Name of loadbalancer
        :param alias: Alias of account
        :param location: Datacenter
        :return: True / False
        """
        changed = False
        lb_exists = self._loadbalancer_exists(name=name)
        if lb_exists:
            result = self.delete_loadbalancer(alias=alias,
                                              location=location,
                                              name=name)
            changed = True
        else:
            result = name
            changed = False
        return changed, result

    def create_loadbalancer(self,name,alias,location,description,status):
        """
        Create a loadbalancer w/ params
        :param name: Name of loadbalancer
        :param alias: Alias of account
        :param location: Datacenter
        :param description: Description for loadbalancer to be created
        :param status: Enabled / Disabled
        :return: Success / Failure
        """
        result = self.clc.v2.API.Call('POST', '/v2/sharedLoadBalancers/%s/%s' % (alias, location), json.dumps({"name":name,"description":description,"status":status}))
        return result

    def delete_loadbalancer(self,alias,location,name):
        """
        Delete CLC loadbalancer
        :param alias: Alias for account
        :param location: Datacenter
        :param name: Name of the loadbalancer to delete
        :return: 204 if successful else failure
        """
        lb_id = self._get_loadbalancer_id(name=name)
        result = self.clc.v2.API.Call('DELETE', '/v2/sharedLoadBalancers/%s/%s/%s' % (alias, location, lb_id))
        return result

    def _get_loadbalancer_id(self, name):
        """
        Retrieve unique ID of loadbalancer
        :param name: Name of loadbalancer
        :return: Unique ID of loadbalancer
        """
        for lb in self.lb_dict:
            if lb.get('name') == name:
                id = lb.get('id')
        return id

    def _get_loadbalancer_list(self, alias, location):
        """
        Retrieve a list of loadbalancers
        :param alias: Alias for account
        :param location: Datacenter
        :return: JSON data for all loadbalancers at datacenter
        """
        return self.clc.v2.API.Call('GET', '/v2/sharedLoadBalancers/%s/%s' % (alias, location))

    def _loadbalancer_exists(self, name):
        """
        Verify a loadbalancer exists
        :param name: Name of loadbalancer
        :return: True / False
        """
        result = False
        if name in [lb.get('name') for lb in self.lb_dict]:
            result = True
        return result

    @staticmethod
    def define_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            name=dict(required=True),
            description=dict(default=None),
            location=dict(default=None),
            alias=dict(default=None),
            status=dict(default='enabled', choices=['enabled', 'disabled']),
            state=dict(default='present', choices=['present', 'absent'])
        )

        return argument_spec

    #
    #   Module Behavior Functions
    #

    def set_clc_credentials_from_env(self):
        """
        Set the CLC Credentials on the sdk by reading environment variables
        :return: none
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

def main():
    module = AnsibleModule(argument_spec=ClcLoadBalancer.define_argument_spec())

    clc_loadbalancer = ClcLoadBalancer(module)
    clc_loadbalancer.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
