# clc-ansible-module

These are additional, unofficial Ansible modules for managing CenturyLink Cloud.

To use this, add this directory to to the ANSIBLE_LIBRARY environment variable, or symlink this directory to ./library underneath the directory containing the playbook that needs it.

## Authentication

In order to use these playbooks, you must set the following environment variables:

```
export CLC_V2_API_USERNAME = <your Control Portal Username>
export CLC_V2_API_PASSWD = <your Control Portal Password>
```


## clc-server Module

Create, delete, start, or stop a server at CLC.  This module can be run in two modes: **idempotent** and **non-idempotent**. The module is idempotent if you specify the *exact_count* and *count_group* parameters.  In that case, it will create or delete the right number of servers to make sure that the number of running VMs in the *count_group* Server Group matches the number specified by the *exact_count* param.  

If you just specify *count* instead of *exact_count*, the module runs in non-idempotent mode.  It will create *count* number of VMs every time it's run.

###Example Playbook```yaml
---
- name: deploy ubuntu hosts at CLC (Yay!)
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Insure that exactly 3 Ubuntu servers are running in Default Group
      clc-server:
        name: test
        template: ubuntu-14-64
        exact_count: 3
        group: 'Default Group'
        count_group: 'Default Group'
      register: clc
    - name: debug
      debug: var=clc.server_ids
```

```yaml
---
- name: deploy ubuntu hosts at CLC (Yay!)
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Deploy 3 new Ubuntu VMs to Default Group
      clc-server:
        name: test
        template: ubuntu-14-64
        count: 3
        group: 'Default Group'
       register: clc
    - name: debug
      debug: var=clc.server_ids
```

###Available Parameters

| Parameter | Required | Default | Choices | Description |
|-----------|:--------:|:-------:|:-------:|-------------|
| `additional_disks:` | N | | | Specify additional disks for the server| `alias:` | N | Username's Alias | | The account alias to provision the servers under.  If an alias is not provided, it will use the account alias of whatever api credentials are provided| `anti_affinity_policy_id:` | N | | | The anti-affinity policy to assign to the server| `count:` | N | | | The number of servers to build (mutually exclusive with `exact_count:`| `count_group:` | N | | | Required when `exact_count:` is specified.  The Server Group use to determine how many severs to deploy.| `cpu:` | N | 1 | | How many CPUs to provision on the server || `cpu_autoscale_policy_id:` | N | | | The autoscale policy to assign to the server.| `custom_fields:` | N | | | A dictionary of custom fields to set on the server.| `description:` | N | Set to `name:` if not provided | | The description to set for the server || `exact_count:` | N | | | Run in *idempotent* mode.  Will insure that this exact number of servers are running in the provided group, creating and deleting them to reach that count.  Requires `count_group:` to be set.| `group:` | N | 'Default Group' | | The Server Group to create servers under.  || `ip_address:` | N | Provided by the platform it not set | | The IP Address for the server. One is assigned if not provided.  This is a parameter on the CLC api, but I'm not sure what happens if it's set.| `location:` | N | Defaults to the default datacenter for the account | | The Datacenter to create servers in.| `managed_os:` | N | N | | Whether to create the server as 'Managed' or not.| `memory:` | N | 1 | Any valid int value | Memory in GB.| `name:` | Y | | | A 1 - 6 character identifier to use for the server.| `network_id:` | N | The first vlan in the datacenter under that account | | The text vlan identifier on which to create the servers.  Defaults if not provided.| `packages:` | N | | | Blueprints to run on the created server.|| `password:` | N | Generated if not provided | | Password for the administrator user.| `primary_dns:` | N | Provided by the platform if not included. | | Primary DNS used by the server. || `secondary_dns:` | N | Provided by the platform if not included. | | Secondary DNS used by the server. || `server_ids:` | Y (for some states)|  |  | Required for `started`, `stopped`, and `absent` states.   A list of server Ids to insure are started, stopped, or absent. | `source_server_password:` | N | | | The password for the source server if a clone is specified || `state:` | Y | | `present`, `started`, `stopped`, `absent` | The state to insure that the provided resources are in.| `storage_type:` | N | `standard` |`standard`, `ssd` | The type of storage to attach to the server.| `template:` | Y |  | any valid template | The template to user for server creation.  Will search for a template if a partial string is provided.  Example: `ubuntu-14-64` will build an Ubuntu 14.04 64bit server.| `ttl:` | N | | Any valid int > 3600 | The time to live for the server.  The server will be deleted when this expires. || `type:` | N | `standard` | `standard`, `hyperscale`| The type of server to create.
| `v2_api_username:` | N | | | The control portal user to use for the task.  ```This should be provided by setting environment variables instead of including it in the playbook.```
| `v2_api_passwd:` | N | | | The control portal password to use for the task.  ```This should be provided by setting environment variables instead of including it in the playbook.```| `wait:` | N | True | Boolean| Whether to wait for the provisioning tasks to finish before returning.




## clc-auth-key Module

Push a SSH key to a user's authorized keys file on a list of servers.  Uses the CLC Server.Credentials API to login.

### Example Playbook
```yaml
---
- name: deploy ubuntu hosts at CLC (Yay!)
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Insure that exactly 3 Ubuntu servers are running in Default Group
      clc-server:
        name: test
        template: ubuntu-14-64
        exact_count: 3
        group: 'Default Group'
        count_group: 'Default Group'
      register: clc

    - name: Deploy ssh key to servers
      clc-auth-key:
        server_ids: "{{ clc.server_ids }}"
        path_to_keyfile: ~/.ssh/id_rsa.pub

    - name: debug
      debug: var=clc.server_ids
```


## Dynamic Inventory Module
