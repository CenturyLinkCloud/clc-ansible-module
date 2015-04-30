#!/usr/bin/python
DOCUMENTATION = '''

'''

EXAMPLES = '''


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

        if not CLC_FOUND:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')

    def process_request(self):
        """
        Execute the main code path, and handle the request
        :return: none
        """
        pass
    #
    #  Functions to define the Ansible module and its arguments
    #

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
