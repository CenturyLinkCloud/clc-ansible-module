#!/usr/bin/python
DOCUMENTATION = '''
'''

EXAMPLES = '''

'''
import sys
import os
import datetime
import json
from time import sleep

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

#
#  An Ansible module to Create, Delete, Start and Stop servers in CenturyLink Cloud.
#
#  Include this file (or symlink to it) in the ./library directory under any playbook that uses it.
#  This is loosely based on the ansible-core-modules EC2 module, and offers similar behavior.
#
#  Ansible requires modules to be self contained, so all of the functions required
#  by this module are included here rather than in a linked common file.  Don't shoot the messenger.
#

#
#  Functions to define the Ansible module and its arguments
#


class ClcServer():
    clc = clc_sdk

    def __init__(self, module):
        """
        Construct module
        """
        self.clc = clc_sdk
        self.module = module
        self.group_dict = {}

        if not CLC_FOUND:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')

    def process_request(self):
        #
        #  Define the module
        #
        p = self.module.params
        state = p['state']

        if not CLC_FOUND:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')

        self.set_clc_credentials_from_env()

        #
        #  Handle each different state
        #

        if state == 'absent':
            server_ids = p['server_ids']
            if not isinstance(server_ids, list):
                self.module.fail_json(
                    msg='termination_list needs to be a list of instances to terminate')

            (changed,
             server_dict_array,
             new_server_ids) = ClcServer._delete_servers(module=self.module,
                                                         clc=self.clc,
                                                         server_ids=server_ids)

        elif state in ('started', 'stopped'):
            server_ids = p['server_ids']
            if not isinstance(server_ids, list):
                self.module.fail_json(
                    msg='running list needs to be a list of servers to run: %s' %
                    server_ids)

            (changed,
             server_dict_array,
             new_server_ids) = ClcServer._startstop_servers(self.module,
                                                            self.clc,
                                                            server_ids,
                                                            state)

        elif state == 'present':
            # Changed is always set to true when provisioning new instances
            if not p['template']:
                self.module.fail_json(
                    msg='template parameter is required for new instance')

            if p['exact_count'] is None:
                (server_dict_array,
                 new_server_ids,
                 changed) = ClcServer._create_servers(self.module,
                                                      self.clc)
            else:
                (server_dict_array,
                 new_server_ids,
                 changed) = ClcServer._enforce_count(self.module,
                                                     self.clc)

        self.module.exit_json(
            changed=changed,
            server_ids=new_server_ids,
            servers=server_dict_array)

    @staticmethod
    def define_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(name=dict(),
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
                             wait=dict(type='bool', default=True))

        mutually_exclusive = [
                                ['exact_count', 'count'],
                                ['exact_count', 'state']
                             ]
        return {"argument_spec": argument_spec,
                "mutually_exclusive": mutually_exclusive}

    def set_clc_credentials_from_env(self):
        """
        Set the CLC Credentials on the sdk by reading environment variables
        :return: none
        """
        env = os.environ
        v2_api_token = env.get('Authorization', False)
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

#
#  Functions to execute the module's behaviors
#  (called from main())
#

    @staticmethod
    def _enforce_count(module, clc):
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
            module.fail_json(
                msg="you must use the 'count_group' option with exact_count")

        servers, running_servers = _find_running_servers_by_group(
            module, clc, datacenter, count_group)

        if len(running_servers) == exact_count:
            changed = False

        elif len(running_servers) < exact_count:
            changed = True
            to_create = exact_count - len(running_servers)
            if not checkmode:
                server_dict_array, changed_server_ids, changed \
                    = ClcServer._create_servers(module, clc, override_count=to_create)

                for server in server_dict_array:
                    running_servers.append(server)

        elif len(running_servers) > exact_count:
            changed = True
            to_remove = len(running_servers) - exact_count
            if not checkmode:
                all_server_ids = sorted([x.id for x in running_servers])
                remove_ids = all_server_ids[0:to_remove]

                (changed, server_dict_array, changed_server_ids) \
                    = ClcServer._delete_servers(module, clc, remove_ids)

        return server_dict_array, changed_server_ids, changed

    @staticmethod
    def _wait_for_requests(clc, requests, servers, wait):
        if wait:
            # Requests.WaitUntilComplete() returns the count of failed requests
            failed_requests_count = sum([request.WaitUntilComplete() for request in requests])

            if failed_requests_count > 0:
                raise clc
            else:
                ClcServer._refresh_servers(servers)

    @staticmethod
    def _create_servers(module, clc, override_count=None):
        """
        Creates new servers

        module : AnsibleModule object
        clc : authenticated CLC connection

        Returns:
            A list of dictionaries with server information
            about the instances that were launched
        """
        p = module.params
        requests = []
        servers = []
        server_dict_array = []
        created_server_ids = []

        add_public_ip = p['add_public_ip']
        public_ip_protocol = p['public_ip_protocol']
        public_ip_ports = p['public_ip_ports']
        wait = p['wait']

        datacenter = _find_datacenter(module, clc)

        network_id = p['network_id'] if p['network_id'] else _find_default_network_id(module, clc, datacenter)

        params = {
            'clc': clc,
            'name': _validate_name(module),
            'template': _find_template_id(module, clc, datacenter),
            'group_id': _find_group(module, clc, datacenter).id,
            'network_id': network_id,
            'cpu': p['cpu'],
            'memory': p['memory'],
            'alias': p['alias'],
            'password': p['password'],
            'ip_address': p['ip_address'],
            'storage_type': p['storage_type'],
            'type': p['type'],
            'primary_dns': p['primary_dns'],
            'secondary_dns': p['secondary_dns'],
            'additional_disks': p['additional_disks'],
            'custom_fields': p['custom_fields'],
            'ttl': p['ttl'],
            'managed_os': p['managed_os'],
            'description': p['description'],
            'source_server_password': p['source_server_password'],
            'cpu_autoscale_policy_id': p['cpu_autoscale_policy_id'],
            'anti_affinity_policy_id': p['anti_affinity_policy_id'],
            'packages': p['packages']
        }

        count = override_count if override_count else p['count']

        changed = False if count == 0 else True

        if changed:
            for i in range(0, count):
                req = create_clc_server(**params)
                server = req.requests[0].Server()
                requests.append(req)
                servers.append(server)

            ClcServer._wait_for_requests(clc, requests, servers, wait)

            ClcServer._add_public_ip_to_servers(
                should_add_public_ip=add_public_ip,
                servers=servers,
                public_ip_protocol=public_ip_protocol,
                public_ip_ports=public_ip_ports,
                wait=wait)

            for server in servers:
                # reload server details so public IP shows up
                server = clc.v2.Server(server.id)
                if len(server.PublicIPs().public_ips) > 0:
                    server.data['publicip'] = str(server.PublicIPs().public_ips[0])
                server.data['ipaddress'] = server.details[
                    'ipAddresses'][0]['internal']
                server_dict_array.append(server.data)
                created_server_ids.append(server.id)

        return server_dict_array, created_server_ids, changed


    @staticmethod
    def _refresh_servers(servers):
        for server in servers:
            server.Refresh()

    @staticmethod
    def _add_public_ip_to_servers(
            should_add_public_ip,
            servers,
            public_ip_protocol,
            public_ip_ports,
            wait):

        if should_add_public_ip:
            ports_lst = []
            requests = []

            for port in public_ip_ports:
                ports_lst.append({'protocol': public_ip_protocol, 'port': port})

            for server in servers:
                requests.append(server.PublicIPs().Add(ports_lst))

            if wait:
                for r in requests:
                    r.WaitUntilComplete()

    @staticmethod
    def _delete_servers(module, clc, server_ids):
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
            module.fail_json(
            module.fail_json(
                msg='server_ids should be a list of servers, aborting'))

        servers = clc.v2.Servers(server_ids).Servers()
        changed = True

        for server in servers:
            requests.append(server.Delete())

        if wait:
            for r in requests:
                r.WaitUntilComplete()

        for server in servers:
            terminated_server_ids.append(server.id)

        return changed, server_dict_array, terminated_server_ids

    @staticmethod
    def _reset_server_power_state(module, server, state):
        result = None
        try:
            if state == 'started':
                result=server.PowerOn()
            else:
                result=server.PowerOff()
        except:
            module.fail_json(
                msg='Unable to change state for server {0}'.format(
                    server.id))
            return result
        return result

    @staticmethod
    def _startstop_servers(module, clc, server_ids, state):
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
            module.fail_json(
                msg='server_ids should be a list of servers, aborting')

        servers=clc.v2.Servers(server_ids).Servers()
        for server in servers:
            if server.powerState != state:
                changed_servers.append(server)
                requests.append(ClcServer._reset_server_power_state(module, server, state))
                changed = True

        if wait:
            for r in requests:
                r.WaitUntilComplete()
            for server in changed_servers:
                server.Refresh()

        for server in changed_servers:
            server_dict_array.append(server.data)
            result_server_ids.append(server.id)

        return changed, server_dict_array, result_server_ids

#
#  Utility Functions
#

def _find_running_servers_by_group(module, clc, datacenter, count_group):
    group = _find_group(
        module=module,
        clc=clc,
        datacenter=datacenter,
        lookup_group=count_group)

    servers = group.Servers().Servers()
    running_servers = []

    for server in servers:
        if server.status == 'active' and server.powerState == 'started':
            running_servers.append(server)

    return servers, running_servers


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
    result = _find_group_recursive(
        module,
        clc,
        datacenter.Groups(),
        lookup_group)

    if result is None:
        module.fail_json(
            msg=str(
                "Unable to find group: " +
                lookup_group +
                " in location: " +
                datacenter.id))

    return result


def _find_group_recursive(module, clc, group_list, lookup_group):
    result = None
    for group in group_list.groups:
        next_victims = group.Subgroups()
        try:
            return next_victims.Get(lookup_group)
        except:
            result = _find_group_recursive(
                module,
                clc,
                next_victims,
                lookup_group)

        if result is not None:
            break

    return result


def _find_template_id(module, clc, datacenter):
    lookup_template = module.params['template']
    result = None
    try:
        result = datacenter.Templates().Search(lookup_template)[0]
    except:
        module.fail_json(
            msg=str(
                "Unable to find a template: " +
                lookup_template +
                " in location: " +
                datacenter.id))
        return result
    return result.id


def _find_default_network_id(module, clc, datacenter):
    result = None
    try:
        result = datacenter.Networks().networks[0]
    except:
        module.fail_json(
            msg=str(
                "Unable to find a network in location: " +
                datacenter.id))
        return result

    return result.id


def _validate_name(module):
    name = module.params['name']
    if len(name) < 1 or len(name) > 6:
        module.fail_json(msg=str(
            "name must be a string with a minimum length of 1 and a maximum length of 6"))

    return name

#
#  This is a hack.  The clc-python-sdk has a defect in its Server.Create function.  It submits a server create request
#  and returns a Request object, but that Request is broken and unable to reference the server that is being created.
#
#  To work around it, we copied the Server.Create function here from the sdk, and then monkey patch the Request object
#  with a working Server() function before it's returned.  We'll submit a PR to the
#  clc-sdk team then remove this code.
#


def create_clc_server(
        clc,
        name,
        template,
        group_id,
        network_id,
        cpu=None,
        memory=None,
        alias=None,
        password=None,
        ip_address=None,
        storage_type="standard",
        type="standard",
        primary_dns=None,
        secondary_dns=None,
        additional_disks=[],
        custom_fields=[],
        ttl=None,
        managed_os=False,
        description=None,
        source_server_password=None,
        cpu_autoscale_policy_id=None,
        anti_affinity_policy_id=None,
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

    if not alias:
        alias = clc.v2.Account.GetAlias()

    if not cpu or not memory:
        group = clc.v2.Group(id=group_id, alias=alias)
        if not cpu and group.Defaults("cpu"):
            cpu = group.Defaults("cpu")
        elif not cpu:
            raise clc

        if not memory and group.Defaults("memory"):
            memory = group.Defaults("memory")
        elif not memory:
            raise clc
    if not description:
        description = name
    if type.lower() not in ("standard", "hyperscale"):
        raise clc
    if type.lower() == "standard" and storage_type.lower() not in (
            "standard",
            "premium"):
        raise clc
    if type.lower() == "hyperscale" and storage_type.lower() != "hyperscale":
        raise clc
    if ttl and ttl <= 3600:
        raise clc
    if ttl:
        ttl = clc.v2.time_utils.SecondsToZuluTS(int(time.time()) + ttl)
    # TODO - validate custom_fields as a list of dicts with an id and a value key
    # TODO - validate template exists
    # TODO - validate additional_disks as a list of dicts with a path, sizeGB, and type (partitioned,raw) keys
    # TODO - validate addition_disks path not in template reserved paths
    # TODO - validate antiaffinity policy id set only with type=hyperscale

    res = clc.v2.API.Call(method='POST',
                          url='servers/%s' % (alias),
                          payload=json.dumps({'name': name,
                                              'description': description,
                                              'groupId': group_id,
                                              'sourceServerId': template,
                                              'isManagedOS': managed_os,
                                              'primaryDNS': primary_dns,
                                              'secondaryDNS': secondary_dns,
                                              'networkId': network_id,
                                              'ipAddress': ip_address,
                                              'password': password,
                                              'sourceServerPassword': source_server_password,
                                              'cpu': cpu,
                                              'cpuAutoscalePolicyId': cpu_autoscale_policy_id,
                                              'memoryGB': memory,
                                              'type': type,
                                              'storageType': storage_type,
                                              'antiAffinityPolicyId': anti_affinity_policy_id,
                                              'customFields': custom_fields,
                                              'additionalDisks': additional_disks,
                                              'ttl': ttl,
                                              'packages': packages}))

    result = clc.v2.Requests(res)

    #
    # Interrupt the method and monkey patch the Request object so it returns a valid server
    #
    # The CLC Python SDK is broken.  We shouldn't have to do this.
    #

    # Find the server's UUID from the API response
    server_uuid = [obj['id']
                   for obj in res['links'] if obj['rel'] == 'self'][0]

    # Change the request server method to a find_server_by_uuid closure so
    # that it will work
    result.requests[0].Server = lambda: find_server_by_uuid(
        clc,
        server_uuid,
        alias)

    return result

#
#  This is the function that gets patched to the Request.server object using a lamda closure
#


def find_server_by_uuid(clc, svr_uuid, alias=None):
    if not alias:
        alias = clc.v2.Account.GetAlias()

    attempts = 5
    backout = 2

    while True:
        attempts -= 1
        try:
            server_obj = clc.v2.API.Call(
                'GET', 'servers/%s/%s?uuid=true' %
                (alias, svr_uuid))
            server_id = server_obj['id']
            server = clc.v2.Server(
                id=server_id,
                alias=alias,
                server_obj=server_obj)
            return server

        except clc.APIFailedResponse as e:
            if e.response_status_code != 404:
                raise e
            if attempts == 0:
                raise e

            sleep(backout)
            backout = backout * 2


def modify_clc_server(clc, acct_alias, server_id, cpu, memory):
    if not acct_alias:
        acct_alias = clc.v2.Account.GetAlias()
    if not server_id:
        raise clc
    # Fetch the existing server information
    server = clc.v2.Server(server_id)

    current_memory = server.memory
    current_cpu = server.cpu
    if memory != current_memory or cpu != current_cpu:
        job_obj = clc.v2.API.Call('PATCH',
                                  'servers/%s/%s' % (acct_alias,
                                                     server_id),
                                  json.dumps([{"op": "set",
                                               "member": "memory",
                                               "value": memory},
                                              {"op": "set",
                                               "member": "cpu",
                                               "value": cpu}]))
        result = clc.v2.Requests(job_obj)
        return result


def main():
    argument_dict = ClcServer.define_argument_spec()
    module = AnsibleModule(**argument_dict)

    clc_server = ClcServer(module)
    clc_server.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
