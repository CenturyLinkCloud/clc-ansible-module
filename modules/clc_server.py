#!/usr/bin/python
DOCUMENTATION = '''
module: clc_server
short_desciption: Create, Delete, Start and Stop servers in CenturyLink Cloud.
description:
  - An Ansible module to Create, Delete, Start and Stop servers in CenturyLink Cloud.
options:
  additional_disks:
    description:
      - Specify additional disks for the server
    required: False
    default: None
    aliases: []
  add_public_ip:
    description:
      - Whether to add a public ip to the server
    required: False
    default: False
    choices: [False, True]
    aliases: []
  alias:
    description:
      - The account alias to provision the servers under.
    default:
      - The default alias for the API credentials
    required: False
    default: None
    aliases: []
  anti_affinity_policy_id:
    description:
      - The anti-affinity policy to assign to the server
    required: False
    default: None
    aliases: []
  count:
    description:
      - The number of servers to build (mutually exclusive with exact_count)
    default: None
    aliases: []
  count_group:
    description:
      - Required when exact_count is specified.  The Server Group use to determine how many severs to deploy.
    default: 1
    required: False
    aliases: []
  cpu:
    description:
      - How many CPUs to provision on the server
    default: None
    required: False
    aliases: []
  cpu_autoscale_policy_id:
    description:
      - The autoscale policy to assign to the server.
    default: None
    required: False
    aliases: []
  custom_fields:
    description:
      - A dictionary of custom fields to set on the server.
    default: []
    required: False
    aliases: []
  description:
    description:
      - The description to set for the server.
    default: None
    required: False
    aliases: []
  exact_count:
    description:
      - Run in idempotent mode.  Will insure that this exact number of servers are running in the provided group, creating and deleting them to reach that count.  Requires count_group to be set.
    default: None
    required: False
    aliases: []
  group:
    description:
      - The Server Group to create servers under.
    default: 'Default Group'
    required: False
    aliases: []
  ip_address:
    description:
      - The IP Address for the server. One is assigned if not provided.
    default: None
    required: False
    aliases: []
  location:
    description:
      - The Datacenter to create servers in.
    default: None
    required: False
    aliases: []
  managed_os:
    description:
      - Whether to create the server as 'Managed' or not.
    default: False
    required: False
    choices: [True, False]
    aliases: []
  memory:
    description:
      - Memory in GB.
    default: 1
    required: False
    aliases: []
  name:
    description:
      - A 1 to 6 character identifier to use for the server.
    default: None
    required: False
    aliases: []
  network_id:
    description:
      - The network UUID on which to create servers.
    default: None
    required: False
    aliases: []
  packages:
    description:
      - Blueprints to run on the server after its created.
    default: []
    required: False
    aliases: []
  password:
    description:
      - Password for the administrator user
    default: None
    required: False
    aliases: []
  primary_dns:
    description:
      - Primary DNS used by the server.
    default: None
    required: False
    aliases: []
  public_ip_protocol:
    description:
      - The protocol to use for the public ip if add_public_ip is set to True.
    default: 'TCP'
    required: False
    aliases: []
  public_ip_ports:
    description:
      - A list of ports to allow on the firewall to thes servers public ip, if add_public_ip is set to True.
    default: []
    required: False
    aliases: []
  secondary_dns:
    description:
      - Secondary DNS used by the server.
    default: None
    required: False
    aliases: []
  server_ids:
    description:
      - Required for started, stopped, and absent states. A list of server Ids to insure are started, stopped, or absent.
    default: []
    required: False
    aliases: []
  source_server_password:
    description:
      - The password for the source server if a clone is specified.
    default: None
    required: False
    aliases: []
  state:
    description:
      - The state to insure that the provided resources are in.
    default: 'present'
    required: False
    choices: ['present', 'absent', 'started', 'stopped']
    aliases: []
  storage_type:
    description:
      - The type of storage to attach to the server.
    default: 'standard'
    required: False
    choices: ['standard', 'hyperscale']
    aliases: []
  template:
    description:
      - The template to use for server creation.  Will search for a template if a partial string is provided.
    default: None
    required: false
    aliases: []
  ttl:
    description:
      - The time to live for the server in seconds.  The server will be deleted when this time expires.
    default: None
    required: False
    aliases: []
  type:
    description:
      - The type of server to create.
    default: 'standard'
    required: False
    choices: ['standard', 'hyperscale']
    aliases: []
  wait:
    description:
      - Whether to wait for the provisioning tasks to finish before returning.
    default: True
    required: False
    choices: [ True, False]
    aliases: []
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
        """
        Process the request - Main Code Path
        :return: Returns with either an exit_json or fail_json
        """

        if not CLC_FOUND:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')

        self._set_clc_credentials_from_env()

        self.module.params = ClcServer._validate_module_params(self.clc,
                                                               self.module)
        p = self.module.params
        state = p['state']

        #
        #  Handle each state
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
    def _define_module_argument_spec():
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
                             type=dict(default='standard', choices=['standard', 'hyperscale']),
                             primary_dns=dict(default=None),
                             secondary_dns=dict(default=None),
                             additional_disks=dict(type='list', default=[]),
                             custom_fields=dict(type='list', default=[]),
                             ttl=dict(default=None),
                             managed_os=dict(type='bool', default=False),
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

    def _set_clc_credentials_from_env(self):
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

    @staticmethod
    def _validate_module_params(clc, module):
        params = module.params
        datacenter = ClcServer._find_datacenter(clc, module)

        ClcServer._validate_types(module)
        ClcServer._validate_name(module)

        params['alias']          = ClcServer._find_alias(clc, module)
        params['cpu']            = ClcServer._find_cpu(clc, module)
        params['memory']         = ClcServer._find_memory(clc, module)
        params['description']    = ClcServer._find_description(module)
        params['ttl']            = ClcServer._find_ttl(clc, module)
        params['template']       = ClcServer._find_template_id(module, datacenter)
        params['group']          = ClcServer._find_group(module, datacenter).id
        params['network_id']     = ClcServer._find_network_id(module, datacenter)

        return params

    @staticmethod
    def _find_datacenter(clc, module):
        location = module.params['location']
        try:
            datacenter = clc.v2.Datacenter(location)
            return datacenter
        except CLCException:
            module.fail_json(msg=str("Unable to find location: " + location))

    @staticmethod
    def _find_alias(clc, module):
        alias  = module.params.get('alias')
        if not alias:
            alias = clc.v2.Account.GetAlias()
        return alias

    @staticmethod
    def _find_cpu(clc, module):
        cpu = module.params.get('cpu')
        group_id = module.params.get('group_id')
        alias = module.params.get('alias')
        state = module.params.get('state')

        if not cpu and state == 'present':
            group = clc.v2.Group(id=group_id,
                                 alias=alias)
            if group.Defaults("cpu"):
                cpu = group.Defaults("cpu")
            else:
                module.fail_json(msg=str("Cannot determine a default cpu value. Please provide a value for cpu."))
        return cpu

    @staticmethod
    def _find_memory(clc, module):
        memory = module.params.get('memory')
        group_id = module.params.get('group_id')
        alias = module.params.get('alias')
        state = module.params.get('state')

        if not memory and state == 'present':
            group = clc.v2.Group(id=group_id,
                                 alias=alias)
            if group.Defaults("memory"):
                memory = group.Defaults("memory")
            else:
                module.fail_json(msg=str("Cannot determine a default memory value. Please provide a value for memory."))
        return memory

    @staticmethod
    def _find_description(module):
        description = module.params.get('description')
        if not description:
            description = module.params.get('name')
        return description

    @staticmethod
    def _validate_types(module):
        state = module.params['state']
        type = module.params.get('type').lower()
        storage_type = module.params.get('storage_type').lower()

        if state == "present":
            if type == "standard" and storage_type not in ("standard", "premium"):
                module.fail_json(msg=str("Standard VMs must have storage_type = 'standard' or 'premium'"))

            if type == "hyperscale" and storage_type != "hyperscale":
                module.fail_json(msg=str("Hyperscale VMs must have storage_type = 'hyperscale'"))

    @staticmethod
    def _find_ttl(clc, module):
        ttl = module.params.get('ttl')

        if ttl:
            if ttl <= 3600:
                module.fail_json(msg=str("Ttl cannot be <= 3600"))
            else:
                ttl = clc.v2.time_utils.SecondsToZuluTS(int(time.time()) + ttl)
        return ttl

    # TODO: Refactor except
    @staticmethod
    def _find_template_id(module, datacenter):
        lookup_template = module.params['template']
        state = module.params['state']
        result = None

        if state == 'present':
            try:
                result = datacenter.Templates().Search(lookup_template)[0].id
            except CLCException:
                module.fail_json(
                    msg=str(
                        "Unable to find a template: " +
                        lookup_template +
                        " in location: " +
                        datacenter.id))
        return result

    @staticmethod
    def _find_network_id(module, datacenter):
        network_id = module.params.get('network_id')

        if not network_id:
            try:
                network_id = datacenter.Networks().networks[0].id
            except CLCException:
                module.fail_json(
                    msg=str(
                        "Unable to find a network in location: " +
                        datacenter.id))

        return network_id

    @staticmethod
    def _validate_name(module):
        name = module.params['name']
        state = module.params['state']

        if state == 'present' and (len(name) < 1 or len(name) > 6):
                module.fail_json(msg=str(
                    "When state = 'present', name must be a string with a minimum length of 1 and a maximum length of 6"))

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
        datacenter = ClcServer._find_datacenter(clc, module)
        exact_count = p['exact_count']
        server_dict_array = []

        # fail here if the exact count was specified without filtering
        # on a group, as this may lead to a undesired removal of instances
        if exact_count and count_group is None:
            module.fail_json(
                msg="you must use the 'count_group' option with exact_count")

        servers, running_servers = ClcServer._find_running_servers_by_group(module, datacenter, count_group)

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

        params = {
            'name': p['name'],
            'template': p['template'],
            'group_id': p['group'],
            'network_id': p['network_id'],
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
                req = ClcServer._create_clc_server(clc, params)
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

        servers = clc.v2.Servers(server_ids).Servers()
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
    @staticmethod
    def _find_running_servers_by_group(module, datacenter, count_group):
        group = ClcServer._find_group(module=module, datacenter=datacenter, lookup_group=count_group)

        servers = group.Servers().Servers()
        running_servers = []

        for server in servers:
            if server.status == 'active' and server.powerState == 'started':
                running_servers.append(server)

        return servers, running_servers

    @staticmethod
    def _find_group(module, datacenter, lookup_group=None):
        result = None
        if not lookup_group:
            lookup_group = module.params['group']
        try:
            return datacenter.Groups().Get(lookup_group)
        except:
            pass

        # The search above only acts on the main
        result = ClcServer._find_group_recursive(module, datacenter.Groups(), lookup_group)

        if result is None:
            module.fail_json(
                msg=str(
                    "Unable to find group: " +
                    lookup_group +
                    " in location: " +
                    datacenter.id))

        return result

    @staticmethod
    def _find_group_recursive(module, group_list, lookup_group):
        result = None
        for group in group_list.groups:
            subgroups = group.Subgroups()
            try:
                return subgroups.Get(lookup_group)
            except:
                result = ClcServer._find_group_recursive(module, subgroups, lookup_group)

            if result is not None:
                break

        return result


    @staticmethod
    def _create_clc_server(
            clc,
            server_params):
        """
        Call the CLC Rest API to Create a Server
        :param clc: the clc-python-sdk instance to use
        :param server_params: a dictionary of params to use to create the servers
        :return: clc-sdk.Request object linked to the queued server request
        """

        res = clc.v2.API.Call(method='POST',
                              url='servers/%s' % (server_params.get('alias')),
                              payload=json.dumps({'name': server_params.get('name'),
                                                  'description': server_params.get('description'),
                                                  'groupId': server_params.get('group_id'),
                                                  'sourceServerId': server_params.get('template'),
                                                  'isManagedOS': server_params.get('managed_os'),
                                                  'primaryDNS': server_params.get('primary_dns'),
                                                  'secondaryDNS': server_params.get('secondary_dns'),
                                                  'networkId': server_params.get('network_id'),
                                                  'ipAddress': server_params.get('ip_address'),
                                                  'password': server_params.get('password'),
                                                  'sourceServerPassword': server_params.get('source_server_password'),
                                                  'cpu': server_params.get('cpu'),
                                                  'cpuAutoscalePolicyId': server_params.get('cpu_autoscale_policy_id'),
                                                  'memoryGB': server_params.get('memory'),
                                                  'type': server_params.get('type'),
                                                  'storageType': server_params.get('storage_type'),
                                                  'antiAffinityPolicyId': server_params.get('anti_affinity_policy_id'),
                                                  'customFields': server_params.get('custom_fields'),
                                                  'additionalDisks': server_params.get('additional_disks'),
                                                  'ttl': server_params.get('ttl'),
                                                  'packages': server_params.get('packages')}))

        result = clc.v2.Requests(res)

        #
        # Patch the Request object so that it returns a valid server

        # Find the server's UUID from the API response
        server_uuid = [obj['id']
                       for obj in res['links'] if obj['rel'] == 'self'][0]

        # Change the request server method to a _find_server_by_uuid closure so
        # that it will work
        result.requests[0].Server = lambda: ClcServer._find_server_by_uuid_w_retry(
            clc,
            server_uuid,
            server_params.get('alias'))

        return result

    #
    #  This is the function that gets patched to the Request.server object using a lamda closure
    #

    @staticmethod
    def _find_server_by_uuid_w_retry(clc, svr_uuid, alias=None):
        if not alias:
            alias = clc.v2.Account.GetAlias()

        attempts = 5
        backout = 2

        # Wait and retry if the api returns a 404
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

    @staticmethod
    def _modify_clc_server(clc, acct_alias, server_id, cpu, memory):
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
    argument_dict = ClcServer._define_module_argument_spec()
    module = AnsibleModule(**argument_dict)

    clc_server = ClcServer(module)
    clc_server.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
