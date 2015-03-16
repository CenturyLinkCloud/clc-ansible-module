#!/usr/bin/python

import sys
import os
import datetime
import json
import paramiko
from ansible.module_utils.basic import *

#
#  Requires the clc-python-sdk.
#  sudo pip install clc-sdk
#
try:
    import clc
except ImportError:
    print "failed=True msg='clc-python-sdk required for this module'"
    sys.exit(1)

#
#  An Ansible module to push SSH keys to a list of servers on CenturyLink Cloud.
#  Include this file (or symlink to it) in the ./library directory under any playbook that uses it.
#  This is loosely based on the ansible-core-modules EC2 module, and offers similar behavior.
#
#  Ansible requires modules to be self contained, so all of the functions required
#  by this module are included here rather than in a linked common file.  Don't shoot the messenger.
#
#  TODO:  Create a pip package for this module, and for common functions

#
#  main() defines the program flow and behaviors
#
def main():

    module = create_ansible_module()
    clc = _clc_set_credentials(module)
    p = module.params

    server_ids = p['server_ids']
    ssh_port = p['ssh_port']
    user_to_update = p['user_to_update']
    path_to_keyfile = p['path_to_keyfile']

    if not isinstance(server_ids, list) or len(server_ids) < 1:
        module.fail_json(msg='server_ids should be a list of servers, aborting')

    key = load_ssh_key(module, path_to_keyfile)
    servers = find_servers(clc, server_ids)
    update_servers(clc, servers, ssh_port, key)

    module.exit_json(changed=True, server_ids=server_ids)

#
#  Functions to define the Ansible module and its arguments
#

def load_ssh_key(module, path_to_keyfile):
    try:
        key = open(os.path.expanduser(path_to_keyfile)).read()
    except IOError as e:
        module.fail_json(msg='unable to load ssh key: %s' % e)
    return key

def create_ansible_module():
    argument_spec = define_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive = [
                                ['path_to_keyfile', 'keystring']
                             ]
    )
    return module

def define_argument_spec():
    argument_spec = clc_common_argument_spec()
    argument_spec.update(
        dict(
            server_ids = dict(type='list'),
            ssh_port = dict(default=22),
            user_to_update = dict(),
            path_to_keyfile = dict(default='~/.ssh/id_rsa.pub'),
            )

    )
    return argument_spec

def clc_common_argument_spec():
    return dict(
        v1_api_key=dict(),
        v1_api_passwd=dict(no_log=True),
        v2_api_username = dict(),
        v2_api_passwd = dict(no_log=True)
    )

#
#  Functions to execute the module's behaviors
#  (called from main())
#

def find_servers(clc, server_ids):
    return clc.v2.Servers(server_ids).Servers()

def update_servers(clc, servers, ssh_port, key):
    for server in servers:
        creds = server.Credentials()

        username = creds['userName']
        password = creds['password']
        ipaddress = server.details['ipAddresses'][0]['internal']

        deploy_key(key ,ipaddress, ssh_port, username, password)

def deploy_key(key, server, ssh_port, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port=ssh_port, username=username, password=password)
    client.exec_command('mkdir -p ~/.ssh/')
    client.exec_command('grep -q -F "%s" foo.bar || echo "%s" >> ~/.ssh/authorized_keys' % (key,key))
    client.exec_command('chmod 644 ~/.ssh/authorized_keys')
    client.exec_command('chmod 700 ~/.ssh/')

#
#  Utility Functions
#

def _clc_set_credentials(module):
        p = module.params
        e = os.environ

        v1_api_key = p['v1_api_key'] if p['v1_api_key'] else e['CLC_V1_API_KEY']
        v1_api_passwd = p['v1_api_passwd'] if p['v1_api_passwd'] else e['CLC_V1_API_PASSWD']
        v2_api_username = p['v2_api_username'] if p['v2_api_username'] else e['CLC_V2_API_USERNAME']
        v2_api_passwd = p['v2_api_passwd'] if p['v2_api_passwd'] else e['CLC_V2_API_PASSWD']

        if (not v2_api_username or not v2_api_passwd):
            module.fail_json(msg = "you must set the clc v2 api username and password on the task or using environment variables")
            sys.exit(1)

        clc.v1.SetCredentials(v1_api_key,v1_api_passwd)
        clc.v2.SetCredentials(v2_api_username,v2_api_passwd)

        return clc

#
#  Run the program
#

main()
