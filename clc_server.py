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

#
#  An Ansible module to Create, Delete, Start and Stop servers in CenturyLink Cloud.
#
#  Include this file (or symlink to it) in the ./library directory under any playbook that uses it.
#  This is loosely based on the ansible-core-modules EC2 module, and offers similar behavior.
#
#  Ansible requires modules to be self contained, so all of the functions required
#  by this module are included here rather than in a linked common file.  Don't shoot the messenger.
#
#  TODO:  Create a pip package for this module, and for common functions

#
#  main() defines the program flow and what behaviors happen for each state
#


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


    #
    #  Handle each different state
    #

    if state == 'absent':
        server_ids = p['server_ids']
        if not isinstance(server_ids, list):
            module.fail_json(msg='termination_list needs to be a list of instances to terminate')

        (changed, server_dict_array, new_server_ids) = delete_servers(module, clc, server_ids)

    elif state in ('started', 'stopped'):
        server_ids = p['server_ids']
        if not isinstance(server_ids, list):
            module.fail_json(msg='running list needs to be a list of servers to run: %s' % server_ids)

        (changed, server_dict_array, new_server_ids) = startstop_servers(module, clc, server_ids, state)

    elif state == 'present':
        # Changed is always set to true when provisioning new instances
        if not p['template']:
            module.fail_json(msg='template parameter is required for new instance')

        if p['exact_count'] is None:
            (server_dict_array, new_server_ids, changed) = create_servers(module, clc)
        else:
            (server_dict_array, new_server_ids, changed) = enforce_count(module, clc)

    module.exit_json(changed=changed, server_ids=new_server_ids, servers=server_dict_array)

#
#  Functions to define the Ansible module and its arguments
#


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
            template=dict(),
            group=dict(default='Default Group'),
            network_id=dict(),
            location=dict(default=None),
            cpu=dict(default=1),
            memory=dict(default='1'),
            alias=dict(default=None),
            password=dict(default=None),
            ip_address=dict(default=None),
            storage_type=dict(default='standard'),
            type=dict(default='standard'),
            primary_dns=dict(default=None),
            secondary_dns=dict(default=None),
            additional_disks=dict(type='list', default=[]),
            custom_fields=dict(type='list', default=[]),
            ttl=dict(default=None),
            managed_os=dict(default=False),
            description=dict(default=None),
            source_server_password=dict(default=None),
            cpu_autoscale_policy_id=dict(default=None),
            anti_affinity_policy_id=dict(default=None),
            packages=dict(type='list', default=[]),
            state=dict(default='present', choices=['present', 'absent', 'started', 'stopped']),
            count=dict(type='int', default='1'),
            exact_count=dict(type='int', default=None),
            count_group=dict(),
            server_ids=dict(type='list'),
            add_public_ip=dict(type='bool', default=False),
            public_ip_protocol=dict(default='TCP'),
            public_ip_ports=dict(type='list'),
            wait=dict(type='bool', default=True)
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

#
#  Functions to execute the module's behaviors
#  (called from main())
#


def enforce_count(module, clc):
    """
    Enforces that there is the right number of servers in the provided group.
    Starts or stops servers as necessary.

    module : AnsibleModule object
    clc : authenticated CLC connection

    Returns:
        A list of dictionaries with server information
        about the instances that were launched or deleted
    """
    p = module.params
    changed_server_ids = None
    changed = False
    checkmode = False
    count_group = p['count_group']
    datacenter = _find_datacenter(module, clc)
    exact_count = p['exact_count']
    server_dict_array = []

    # fail here if the exact count was specified without filtering
    # on a group, as this may lead to a undesired removal of instances
    if exact_count and count_group is None:
        module.fail_json(msg="you must use the 'count_group' option with exact_count")

    servers, running_servers = _find_running_servers_by_group_name(module, clc, datacenter, count_group)

    if len(running_servers) == exact_count:
        changed = False
        
    elif len(running_servers) < exact_count:
        changed = True
        to_create = exact_count - len(running_servers)
        if not checkmode:
            (server_dict_array, changed_server_ids, changed) \
                = create_servers(module, clc, override_count=to_create)

            for server in server_dict_array:
                running_servers.append(server)

    elif len(running_servers) > exact_count:
        changed = True
        to_remove = len(running_servers) - exact_count
        if not checkmode:
            all_server_ids = sorted([ x.id for x in running_servers ])
            remove_ids = all_server_ids[0:to_remove]

            (changed, server_dict_array, changed_server_ids) \
                = delete_servers(module, clc, remove_ids)

    return (server_dict_array, changed_server_ids, changed)


def create_servers(module, clc, override_count=None):
    """
    Creates new servers

    module : AnsibleModule object
    clc : authenticated CLC connection

    Returns:
        A list of dictionaries with server information
        about the instances that were launched
    """
    p = module.params
    name = _validate_name(module)

    network_id = p['network_id']
    cpu = p['cpu']
    memory = p['memory']
    alias = p['alias']
    password = p['password']
    ip_address = p['ip_address']
    storage_type = p['storage_type']
    svr_type = p['type']
    primary_dns = p['primary_dns']
    secondary_dns = p['secondary_dns']
    additional_disks = p['additional_disks']
    custom_fields = p['custom_fields']
    ttl = p['ttl']
    managed_os = p['managed_os']
    description = p['description']
    source_server_password = p['source_server_password']
    cpu_autoscale_policy_id = p['cpu_autoscale_policy_id']
    anti_affinity_policy_id = p['anti_affinity_policy_id']
    packages = p['packages']
    add_public_ip = p['add_public_ip']
    public_ip_protocol = p['public_ip_protocol']
    public_ip_ports = p['public_ip_ports']
    wait = p['wait']

    if override_count:
        count = override_count
    else:
        count = p['count']

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
            for server in servers:
                server.Refresh()

        if add_public_ip:
            add_public_ip_to_servers(clc, servers, public_ip_protocol, public_ip_ports, wait)

        for server in servers:
            server = clc.v2.Server(server.id)  # reload server details so public IP shows up
            if len(server.PublicIPs().public_ips) > 0:
                server.data['publicip'] = str(server.PublicIPs().public_ips[0])
            server.data['ipaddress'] = server.details['ipAddresses'][0]['internal']
            server_dict_array.append(server.data)
            created_server_ids.append(server.id)

    return (server_dict_array, created_server_ids, changed)


def delete_servers(module, clc, server_ids):
    """
    Deletes the servers on the provided list

    module: Ansible module object
    clc: authenticated clc connection object
    server_ids: a list of servers to terminate in the form of
      [ {id: <server-id>}, ..]

    Returns a dictionary of server information
    about the servers terminated.

    If the server to be terminated is running
    "changed" will be set to False.

    """
    # Whether to wait for termination to complete before returning
    p = module.params
    wait = p['wait']
    terminated_server_ids = []
    server_dict_array = []
    requests = []

    changed = False
    if not isinstance(server_ids, list) or len(server_ids) < 1:
        module.fail_json(msg='server_ids should be a list of servers, aborting')

    servers = clc.v2.Servers(server_ids).Servers()
    changed = True

    for server in servers:
        requests.append(server.Delete())

    if wait:
        sum(requests).WaitUntilComplete()

    for server in servers:
        terminated_server_ids.append(server.id)

    return (changed, server_dict_array, terminated_server_ids)


def startstop_servers(module, clc, server_ids, state):
    """
    Starts or stops a list of existing servers

    module: Ansible module object
    clc: authenticated ec2 connection object
    server_ids: The list of servers to start in the form of
      [ {id: <server-id>}, ..]
    state: Intended state ("started" or "stopped")

    Returns a dictionary of instance information
    about the servers started/stopped.

    If the instance was not able to change state,
    "changed" will be set to False.
    """
    p = module.params
    wait = p['wait']
    changed = False
    changed_servers = []
    server_dict_array = []
    result_server_ids = []
    requests = []

    if not isinstance(server_ids, list) or len(server_ids) < 1:
        module.fail_json(msg='server_ids should be a list of servers, aborting')

    servers = clc.v2.Servers(server_ids).Servers()
    for server in servers:
        if server.powerState != state:
            changed_servers.append(server)
            try:
                if state=='started':
                    requests.append(server.PowerOn())
                else:
                    requests.append(server.PowerOff())
            except:
                module.fail_json(msg='Unable to change state for server {0}'.format(server.id))
            changed = True

    if wait:
        sum(requests).WaitUntilComplete()
        for server in changed_servers:
            server.Refresh()

    for server in changed_servers:
        server_dict_array.append(server.data)
        result_server_ids.append(server.id)

    return (changed, server_dict_array, result_server_ids)

#
#  Utility Functions
#

def add_public_ip_to_servers(clc, servers, public_ip_protocol, public_ip_ports, wait):
    ports_lst = []
    requests = []

    for port in public_ip_ports:
        ports_lst.append({'protocol': public_ip_protocol, 'port': port})

    for server in servers:
        requests.append(server.PublicIPs().Add(ports_lst))

    if wait:
        sum(requests).WaitUntilComplete()


def _clc_set_credentials(clc, module):
        e = os.environ

        v2_api_passwd = None
        v2_api_username = None

        try:
            v2_api_username = e['CLC_V2_API_USERNAME']
            v2_api_passwd = e['CLC_V2_API_PASSWD']
        except KeyError, e:
            module.fail_json(msg = "you must set the CLC_V2_API_USERNAME and CLC_V2_API_PASSWD environment variables")

        clc.v2.SetCredentials(api_username=v2_api_username, api_passwd=v2_api_passwd)
        return clc


def _find_running_servers_by_group_name(module, clc, datacenter, count_group):
    group = _find_group(module=module, clc=clc, datacenter=datacenter, lookup_group=count_group)

    servers = group.Servers().Servers()
    running_servers = []

    for server in servers:
        if (server.status == 'active' and server.powerState == 'started'):
            running_servers.append(server)

    return servers, running_servers


def _refresh_server_w_retry(server):
    server.Refresh()

def _find_datacenter(module, clc):
    location = module.params['location']
    try:
        datacenter = clc.v2.Datacenter(location)
    except:
        module.fail_json(msg=str("Unable to find location: " + location))
        sys.exit(1)
    return datacenter


def _find_group(module, clc, datacenter, lookup_group=None):
    result = None
    if not lookup_group:
        lookup_group = module.params['group']
    try:
        return datacenter.Groups().Get(lookup_group)
    except:
        pass

    # That search above only acts on the main 
    result = _find_group_recursive(module, clc, datacenter.Groups(), lookup_group)

    if result is None:
        module.fail_json(msg=str("Unable to find group: " + lookup_group + " in location: " + datacenter.id))

    return result

def _find_group_recursive(module, clc, group_list, lookup_group):
    result = None
    for group in group_list.groups:
        next_victims = group.Subgroups()
        try:
            return next_victims.Get(lookup_group)
        except:
            result = _find_group_recursive(module, clc, next_victims, lookup_group)

        if result is not None:
            break

    return result

def _find_template(module,clc,datacenter):
    lookup_template = module.params['template']
    result = None
    try:
        result = datacenter.Templates().Search(lookup_template)[0]
    except:
        module.fail_json(msg=str("Unable to find a template: "+ lookup_template +" in location: " + datacenter.id))

    return result


def _find_default_network(module, clc, datacenter):
    result = None
    try:
        result = datacenter.Networks().networks[0]
    except:
        module.fail_json(msg=str("Unable to find a network in location: " + datacenter.id))

    return result


def _validate_name(module):
    name = module.params['name']
    if (len(name)<1 or len(name) > 6):
        module.fail_json(msg=str("name must be a string with a minimum length of 1 and a maximum length of 6"))

    return name

#
#  This is a hack.  The clc-python-sdk has a defect in its Server.Create function.  It submits a server create request
#  and returns a Request object, but that Request is broken and unable to reference the server that is being created.
#
#  To work around it, we copied the Server.Create function here from the sdk, and then monkey patch the Request object
#  with a working Server() function before it's returned.  We'll submit a PR to the
#  clc-sdk team then remove this code.
#


def create_clc_server(clc, name,template,group_id,network_id,cpu=None,memory=None,alias=None,password=None,ip_address=None,
           storage_type="standard",type="standard",primary_dns=None,secondary_dns=None,
           additional_disks=[],custom_fields=[],ttl=None,managed_os=False,description=None,
           source_server_password=None,cpu_autoscale_policy_id=None,anti_affinity_policy_id=None,
           packages=[]):
    """Creates a new server.

    https://t3n.zendesk.com/entries/59565550-Create-Server

    cpu and memory are optional and if not provided we pull from the default server size values associated with
    the provided group_id.

    Set ttl as number of seconds before server is to be terminated.  Must be >3600

    >>> d = clc.v2.Datacenter()
    >>> clc.v2.Server.Create(name="api2",cpu=1,memory=1,group_id="wa1-4416",
                             template=d.Templates().Search("centos-6-64")[0].id,
                             network_id=d.Networks().networks[0].id).WaitUntilComplete()
    0

    """

    if not alias:  alias = clc.v2.Account.GetAlias()

    if not cpu or not memory:
        group = clc.v2.Group(id=group_id,alias=alias)
        if not cpu and group.Defaults("cpu"):  cpu = group.Defaults("cpu")
        elif not cpu:  raise(clc.CLCException("No default CPU defined"))

        if not memory and group.Defaults("memory"):  memory = group.Defaults("memory")
        elif not memory:  raise(clc.CLCException("No default Memory defined"))
    if not description:  description = name
    if type.lower() not in ("standard","hyperscale"):  raise(clc.CLCException("Invalid type"))
    if type.lower() == "standard" and storage_type.lower() not in ("standard","premium"):  raise(clc.CLCException("Invalid storage_type"))
    if type.lower() == "hyperscale" and storage_type.lower() !=  "hyperscale":  raise(clc.CLCException("Invalid type/storage_type combo"))
    if ttl and ttl<=3600: raise(clc.CLCException("ttl must be greater than 3600 seconds"))
    if ttl: ttl = clc.v2.time_utils.SecondsToZuluTS(int(time.time())+ttl)
    # TODO - validate custom_fields as a list of dicts with an id and a value key
    # TODO - validate template exists
    # TODO - validate additional_disks as a list of dicts with a path, sizeGB, and type (partitioned,raw) keys
    # TODO - validate addition_disks path not in template reserved paths
    # TODO - validate antiaffinity policy id set only with type=hyperscale

    res = clc.v2.API.Call('POST','servers/%s' % (alias),
             json.dumps({'name': name, 'description': description, 'groupId': group_id, 'sourceServerId': template,
                         'isManagedOS': managed_os, 'primaryDNS': primary_dns, 'secondaryDNS': secondary_dns,
                         'networkId': network_id, 'ipAddress': ip_address, 'password': password,
                         'sourceServerPassword': source_server_password, 'cpu': cpu, 'cpuAutoscalePolicyId': cpu_autoscale_policy_id,
                         'memoryGB': memory, 'type': type, 'storageType': storage_type, 'antiAffinityPolicyId': anti_affinity_policy_id,
                         'customFields': custom_fields, 'additionalDisks': additional_disks, 'ttl': ttl, 'packages': packages}))

    result = clc.v2.Requests(res)

    #
    # Interrupt the method and monkey patch the Request object so it returns a valid server
    #
    # The CLC Python SDK is broken.  We shouldn't have to do this.
    #

    # Find the server's UUID from the API response
    server_uuid = [obj['id'] for obj in res['links'] if obj['rel']=='self'][0]

    # Change the request server method to a find_server_by_uuid closure so that it will work
    result.requests[0].Server = lambda: find_server_by_uuid(clc, server_uuid, alias)

    return result

#
#  This is the function that gets patched to the Request.server object using a lamda closure
#


def find_server_by_uuid(clc, svr_uuid, alias=None):
    if not alias:
        alias = clc.v2.Account.GetAlias()

    server_obj = clc.v2.API.Call('GET', 'servers/%s/%s?uuid=true' % (alias,svr_uuid))
    server_id = server_obj['id']
    server = clc.v2.Server(id=server_id, alias=alias, server_obj=server_obj)
    return server

#
#  Run the program
#
if __name__ == '__main__':
    main()
