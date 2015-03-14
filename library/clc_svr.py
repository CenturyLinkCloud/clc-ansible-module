#!/usr/bin/python

import sys
import os
import datetime
import json

sys.path.append(os.path.expanduser('./common'))
from clc_util import *

def find_running_instances_by_group_name(module, clc, count_tag, zone=None):
    return

def _set_none_to_blank(dictionary):
    return

def get_reservations(module, clc, tags=None, state=None, zone=None):
    return

def get_instance_info(inst):
    return

def enforce_count(module, clc, vpc):

    all_instances = []
    instance_dict_array = []
    changed_instance_ids = []
    changed = False

    return (all_instances, instance_dict_array, changed_instance_ids, changed)

def create_instances(module, clc, vpc):
    """
    Creates new instances

    module : AnsibleModule object

    Returns:
        A list of dictionaries with instance information
        about the instances that were launched
    """
    name = module.params.get('name')
    template = module.params.get('template')
    group_id = module.params.get('group_id')
    network_id = module.params.get('network_id')
    cpu = module.params.get('cpu')
    memory = module.params.get('memory')
    alias = module.params.get('alias')
    password = module.params.get('password')
    ip_address = module.params.get('ip_address')
    storage_type = module.params.get('storage_type')
    svr_type = module.params.get('type')
    primary_dns = module.params.get('primary_dns')
    secondary_dns = module.params.get('secondary_dns')
    additional_disks = module.params.get('additional_disks')
    custom_fields = module.params.get('custom_fields')
    ttl = module.params.get('ttl')
    managed_os = module.params.get('managed_os')
    description = module.params.get('description')
    source_server_password = module.params.get('source_server_password')
    cpu_autoscale_policy_id = module.params.get('cpu_autoscale_policy_id')
    anti_affinity_policy_id = module.params.get('anti_affinity_policy_id')
    packages = module.params.get('packages')

    # clc.v2.Server.Create(name, template, group_id, network_id, cpu=None, memory=None, alias=None,
    #                  password=None, ip_address=None, storage_type="standard", type="standard",
    #                  primary_dns=None, secondary_dns=None, additional_disks=[], custom_fields=[],
    #                  ttl=None, managed_os=False, description=None, source_server_password=None,
    #                  cpu_autoscale_policy_id=None, anti_affinity_policy_id=None, packages=[])

    instance_dict_array = []
    created_instance_ids = []
    changed = False

    return (instance_dict_array, created_instance_ids, changed)

def terminate_instances(module, clc, instance_ids):

    changed = False
    instance_dict_array = []
    new_instance_ids = []

    return (changed, instance_dict_array, new_instance_ids)

def startstop_instances(module, clc, instance_ids, state):

    changed = False
    instance_dict_array = []
    new_instance_ids = []

    return (changed, instance_dict_array, new_instance_ids)

def main():

    argument_spec = clc_common_argument_spec()
    argument_spec.update(
        dict(
            name = dict(),
            template = dict(),
            group_id = dict(),
            group_name = dict(),
            network_id = dict(),
            cpu = dict(default=None),
            memory = dict(default=None),
            alias = dict(default=None),
            password = dict(default=None),
            ip_address = dict(default=None),
            storage_type = dict(default='standard'),
            type = dict(default='standard'),
            primary_dns = dict(default=None),
            secondary_dns = dict(default=None),
            additional_disks = dict(type='list', default=[]),
            custom_fields = dict(type='list', default=[]),
            ttl = dict(default=None),
            managed_os = dict(default=False),
            description = dict(default=None),
            source_server_password = dict(default=None),
            cpu_autoscale_policy_id = dict(default=None),
            anti_affinity_policy_id = dict(default=None),
            packages = dict(type='list', default=[]),
            state = dict(default='present', choices=['present', 'absent']),
            count = dict(type='int', default='1'),
            exact_count = dict(type='int', default=None),
            wait = dict(type='bool', default=False),
            wait_timeout = dict(default=300)
            )

    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive = [
                                ['exact_count', 'count'],
                                ['exact_count', 'state'],
                                ['group_id', 'group_name'],
                             ],
    )

    clc = clc_set_credentials(module)

    vpc = None

    state = module.params.get('state')

    if state == 'absent':
        instance_ids = module.params.get('instance_ids')
        if not isinstance(instance_ids, list):
            module.fail_json(msg='termination_list needs to be a list of instances to terminate')

        (changed, instance_dict_array, new_instance_ids) = terminate_instances(module, clc, instance_ids)

    elif state in ('running', 'stopped'):
        instance_ids = module.params.get('instance_ids')
        if not isinstance(instance_ids, list):
            module.fail_json(msg='running list needs to be a list of instances to run: %s' % instance_ids)

        (changed, instance_dict_array, new_instance_ids) = startstop_instances(module, clc, instance_ids, state)

    elif state == 'present':
        # Changed is always set to true when provisioning new instances
        if not module.params.get('template'):
            module.fail_json(msg='template parameter is required for new instance')

        if module.params.get('exact_count') is None:
            (instance_dict_array, new_instance_ids, changed) = create_instances(module, clc, vpc)
        else:
            (tagged_instances, instance_dict_array, new_instance_ids, changed) = enforce_count(module, clc, vpc)

    result = json.dumps(module.params)
    print result

from ansible.module_utils.basic import *
main()
