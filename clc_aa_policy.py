#!/usr/bin/python

import sys
import os
import datetime
import json
from ansible.module_utils.basic import *

#
#  Requires the clc-python-sdk.
#  sudo pip install clc-sdk
#
try:
    import clc as clc_sdk
except ImportError:
    clc_found = False
    clc_sdk = None
else:
    clc_found = True

def main():

    #
    #  Define the module
    #
    module = create_ansible_module()
    p = module.params
    state = p['state']

    if not clc_found:
        module.fail_json(msg='clc-python-sdk required for this module')

    clc = _clc_set_credentials(clc_sdk, module)

    # more to come


def create_ansible_module():
    argument_spec = define_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive = [
                                ['exact_count', 'count'],
                                ['exact_count', 'state']
                             ]
    )
    return module


def define_argument_spec():
    argument_spec = clc_common_argument_spec()
    argument_spec.update(
        dict(
            name=dict(),
            location=dict(default=None),
            state=dict(default='present', choices=['present', 'absent', 'started', 'stopped']),
            )

    )
    return argument_spec


def clc_common_argument_spec():
    return dict(
        v1_api_key=dict(),
        v1_api_passwd=dict(no_log=True),
        v2_api_username=dict(),
        v2_api_passwd=dict(no_log=True)
    )

def _clc_set_credentials(clc, module):
        e = os.environ

        v2_api_passwd = None
        v2_api_username = None

        try:
            v2_api_username = e['CLC_V2_API_USERNAME']
            v2_api_passwd = e['CLC_V2_API_PASSWD']
        except KeyError, e:
            module.fail_json(msg = "Set the CLC_V2_API_USERNAME and CLC_V2_API_PASSWD environment variables or keep seeing this message")

        clc.v2.SetCredentials(api_username=v2_api_username, api_passwd=v2_api_passwd)
        return clc