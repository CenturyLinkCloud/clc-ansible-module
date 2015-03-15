
import json
import os

try:
    import clc
except ImportError:
    print "failed=True msg='clc-python-sdk required for this module'"
    sys.exit(1)


def clc_common_argument_spec():
    return dict(
        v1_api_key=dict(),
        v1_api_passwd=dict(no_log=True),
        v2_api_username = dict(),
        v2_api_passwd = dict(no_log=True)
    )

def clc_set_credentials(module):
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
    if storage_type.lower() not in ("standard","premium"):  raise(clc.CLCException("Invalid storage_type"))
    if storage_type.lower() == "premium" and type.lower() == "hyperscale":  raise(clc.CLCException("Invalid type/storage_type combo"))
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
    # The CLC Python API is broken.  We shouldn't have to do this.
    #

    # Find the server's UUID from the API response
    serverUuid = [obj['id'] for obj in res['links'] if obj['rel']=='self'][0]

    # Change the request server method to a find_server_by_uuid closure so that it will work
    result.requests[0].Server = lambda: find_server_by_uuid(clc, serverUuid, alias)

    return result

def find_server_by_uuid(clc, svr_uuid, alias=None):
    if not alias:  alias = clc_conn.v2.Account.GetAlias()
    server_obj = clc.v2.API.Call('GET','servers/%s/%s?uuid=true' % (alias,svr_uuid))
    server_id = server_obj['id']
    server = clc.v2.Server(id=server_id,alias=alias,server_obj=server_obj)
    return server
