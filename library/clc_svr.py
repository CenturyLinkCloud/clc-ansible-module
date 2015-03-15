#!/usr/bin/python

import sys
import os
import datetime
import json
#import pudb; pu.db

sys.path.append(os.path.expanduser('~/Development/workspace/clc-ansible-module/library/common'))
from clc_util import *

def find_running_servers_by_group_name(module, clc, datacenter, count_group):
    group = _find_group(module, clc, datacenter, count_group)

    servers = group.Servers().Servers()
    running_servers = []

    for server in servers:
        if (server.status == 'active' and server.powerState == 'started'):
            running_servers.append(server)

    return servers, running_servers

def _find_datacenter(module, clc):
    location = module.params.get('location')
    try:
        datacenter = clc.v2.Datacenter(location)
    except:
        module.fail_json(msg = str("Unable to find location: " + location))
        sys.exit(1)
    return datacenter

def _find_group(module, clc, datacenter, lookup_group=None):
    if not lookup_group:
        lookup_group = module.params.get('group')
    try:
        group = datacenter.Groups().Get(lookup_group)
    except:
        module.fail_json(msg = str("Unable to find group: " + lookup_group + " in location: " + datacenter.id))
        sys.exit(1)
    return group

def _find_template(module,clc,datacenter):
    lookup_template = module.params.get('template')
    try:
        template = datacenter.Templates().Search(lookup_template)[0]
    except:
        module.fail_json(msg = str("Unable to find a template: "+ lookup_template +" in location: " + datacenter.id))
        sys.exit(1)
    return template

def _find_default_network(module, clc, datacenter):
    try:
        network = datacenter.Networks().networks[0]
    except:
        module.fail_json(msg = str("Unable to find a network in location: " + datacenter.id))
        sys.exit(1)
    return network

def _validate_name(module):
    name = module.params.get('name')
    if (len(name)<1 or len(name) > 6):
        module.fail_json(msg = str("name must be a string with a minimum length of 1 and a maximum length of 6"))
        sys.exit(1)
    return name

def _set_none_to_blank(dictionary):
    return

def get_reservations(module, clc, tags=None, state=None, zone=None):
    return

def get_instance_info(inst):
    return

def enforce_count(module, clc):

    exact_count = module.params.get('exact_count')
    count_group = module.params.get('count_group')
    datacenter = _find_datacenter(module, clc)

    # fail here if the exact count was specified without filtering
    # on a group, as this may lead to a undesired removal of instances
    if exact_count and count_group is None:
        module.fail_json(msg="you must use the 'count_group' option with exact_count")

    servers, running_servers = find_running_servers_by_group_name(module, clc, datacenter, count_group)

    changed = None
    checkmode = False
    server_dict_array = []
    changed_server_ids = None

    all_servers = []
    changed = False

    if len(running_servers) == exact_count:
        changed = False
    elif len(running_servers) < exact_count:
        changed = True
        to_create = exact_count - len(running_servers)
        if not checkmode:
            (server_dict_array, changed_server_ids, changed) \
                = create_instances(module, clc, override_count=to_create)

            for server in server_dict_array:
                running_servers.append(server)

    return (server_dict_array, changed_server_ids, changed)

def create_instances(module, clc, override_count=None):
    """
    Creates new instances

    module : AnsibleModule object

    Returns:
        A list of dictionaries with instance information
        about the instances that were launched
    """
    name = _validate_name(module)

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
    wait = module.params.get('wait')

    if override_count:
        count = override_count
    else:
        count = module.params.get('count')

    datacenter = _find_datacenter(module, clc)
    group = _find_group(module, clc, datacenter)
    template = _find_template(module, clc, datacenter)

    if not network_id:
        network_id = _find_default_network(module, clc, datacenter).id

    params = {
        'clc': clc,
        'name': name,
        'template': template.id,
        'group_id': group.id,
        'network_id': network_id,
        'cpu': cpu,
        'memory': memory,
        'alias': alias,
        'password': password,
        'ip_address': ip_address,
        'storage_type': storage_type,
        'type': svr_type,
        'primary_dns': primary_dns,
        'secondary_dns': secondary_dns,
        'additional_disks': additional_disks,
        'custom_fields': custom_fields,
        'ttl': ttl,
        'managed_os': managed_os,
        'description': description,
        'source_server_password': source_server_password,
        'cpu_autoscale_policy_id': cpu_autoscale_policy_id,
        'anti_affinity_policy_id': anti_affinity_policy_id,
        'packages': packages
    }

    if count == 0:
        changed = False
    else:
        changed = True

        requests = []
        servers = []
        server_dict_array = []
        created_server_ids = []

        for i in range(0,count):
            req=create_clc_server(**params)
            server = req.requests[0].Server()
            requests.append(req)
            servers.append(server)

        if wait:
            sum(requests).WaitUntilComplete()
            for server in servers: server.Refresh()

        for server in servers:
            server_dict_array.append(server.data)
            created_server_ids.append(server.id)

    return (server_dict_array, created_server_ids, changed)

def terminate_instances(module, clc, instance_ids):

    changed = False
    server_dict_array = []
    new_server_ids = []

    return (changed, server_dict_array, new_server_ids)

def startstop_instances(module, clc, instance_ids, state):

    changed = False
    server_dict_array = []
    new_server_ids = []

    return (changed, server_dict_array, new_server_ids)

def create_ansible_module():
    argument_spec = define_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive = [
                                ['exact_count', 'count'],
                                ['exact_count', 'state']
                             ],
    )
    return module

def define_argument_spec():
    argument_spec = clc_common_argument_spec()
    argument_spec.update(
        dict(
            name = dict(),
            template = dict(),
            group = dict(default='Default Group'),
            network_id = dict(),
            location = dict(default=None),
            cpu = dict(default=1),
            memory = dict(default='1'),
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
            count_group = dict(),
            wait = dict(type='bool', default=True),
            )

    )
    return argument_spec

def main():

    module = create_ansible_module()
    clc = clc_set_credentials(module)
    state = module.params.get('state')

    tagged_instances = []

    if state == 'absent':
        instance_ids = module.params.get('instance_ids')
        if not isinstance(instance_ids, list):
            module.fail_json(msg='termination_list needs to be a list of instances to terminate')

        (changed, server_dict_array, new_server_ids) = terminate_instances(module, clc, instance_ids)

    elif state in ('running', 'stopped'):
        instance_ids = module.params.get('instance_ids')
        if not isinstance(instance_ids, list):
            module.fail_json(msg='running list needs to be a list of instances to run: %s' % instance_ids)

        (changed, server_dict_array, new_server_ids) = startstop_instances(module, clc, instance_ids, state)

    elif state == 'present':
        # Changed is always set to true when provisioning new instances
        if not module.params.get('template'):
            module.fail_json(msg='template parameter is required for new instance')

        if module.params.get('exact_count') is None:
            (server_dict_array, new_server_ids, changed) = create_instances(module, clc)
        else:
            (server_dict_array, new_server_ids, changed) = enforce_count(module, clc)

    module.exit_json(changed=changed, server_ids=new_server_ids, servers=server_dict_array)

from ansible.module_utils.basic import *
main()
