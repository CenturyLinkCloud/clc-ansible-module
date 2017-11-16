![Build Status](http://206.128.156.165/build/status/clc-ansible-module)
# clc-ansible-module

[**NEW! Dynamic Inventory Script**](#dyn_inventory)

These are additional, unofficial Ansible modules for managing CenturyLink Cloud.

### Installation

```bash
sudo pip install clc-ansible-module
```

To use this, add the python dist/site-packages directory to to the ***ANSIBLE_LIBRARY*** environment variable, or symlink this directory to ./library underneath the directory containing the playbook that needs it.

The installation will install a dynamic inventory script to /usr/local/bin.  In order to use the script you will need to fully reference the clc\_inv.py script with each Ansible command.  You can avoid having to enter in this script for each command by creating a symlink in /etc/ansible to this script as such:

```bash
ln -s /usr/local/bin/clc_inv.py /etc/ansible/hosts
```

#### Validation
Validate that the clc-ansible-module package has been installed and is functioning:
```bash
ansible all -i /usr/local/bin/clc_inv.py --list-hosts
```

Validate that all packages are install and configured:
```bash
ansible-playbook -i /usr/local/bin/clc_inv.py my-playbook.yml
```

#### Dependencies
This module has one dependency  The [clc-python-sdk](https://github.com/CenturyLinkCloud/clc-python-sdk).  You can install it with pip

```bash
sudo pip install clc-sdk
```


## Authentication

In order to use these playbooks, you must set the following environment variables:

```bash
export CLC_V2_API_USERNAME=<your Control Portal Username>
export CLC_V2_API_PASSWD=<your Control Portal Password>
```

## clc_server Module

Create, delete, start, or stop a server at CLC.  This module can be run in two modes: **idempotent** and **non-idempotent**. The module is idempotent if you specify the *exact_count* and *count_group* parameters.  In that case, it will create or delete the right number of servers to make sure that the number of running VMs in the *count_group* Server Group matches the number specified by the *exact_count* param.  

If you just specify *count* instead of *exact_count*, the module runs in non-idempotent mode.  It will create *count* number of VMs every time it's run.

### Example Playbooks
```yaml
---
- name: deploy ubuntu hosts at CLC (Yay!)
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Insure that exactly 3 Ubuntu servers are running in Default Group
      clc_server:
        name: test
        template: ubuntu-14-64
        exact_count: 3
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
      clc_server:
        name: test
        template: ubuntu-14-64
        count: 3
        group: 'Default Group'
       register: clc
    - name: debug
      debug: var=clc.server_ids
```

```yaml
---
- name: Create a Linux Server with 3 GBs of app space
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create Server
      clc_server:
        name: test
        template: ubuntu-14-64
        count: 1
        group: 'Default Group'
        additional_disks:
          - {path: /myApp, sizeGB: 3, type: partitioned}
      register: clc
    - name: debug
      debug: var=clc
```

```yaml
---
- name: Sample playbook which executes a blueprint package post build.
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create Server
      clc_server:
        name: test
        description: 'Test Server'
        template: WIN2012R2DTC-64
        group: 'Default Group'
        count: 1
        cpu: 2
        memory: 4
        additional_disks:
          - {path: e, sizeGB: 100, type: partitioned}
        packages:
          - { packageId: '98d7cb38-41ae-41de-b3e4-9967be006f6c', parameters: {} }
      register: clc_svr
    - debug: var=clc_svr
```

### Available Parameters

| Parameter | Required | Default | Choices | Description |
|-----------|:--------:|:-------:|:-------:|-------------|
| `additional_disks:` | N | | | Specify additional disks for the server.  
| `alias:` | N | Username's Alias | | The account alias to provision the servers under.  If an alias is not provided, it will use the account alias of whatever api credentials are provided
| `anti_affinity_policy_id:` | N | | | The anti-affinity policy id to assign to the server. This is mutually exclusive with `anti_affinity_policy_name:`
| `anti_affinity_policy_name:` | N | | | The anti-affinity policy name to assign to the server. This is mutually exclusive with `anti_affinity_policy_id:`
| `alert_policy_id:` | N | | | The alert policy id to assign to the server. This is mutually exclusive with `alert_policy_name:`
| `alert_policy_name:` | N | | | The alert policy name to assign to the server. This is mutually exclusive with `alert_policy_id:`
| `count:` | N | | | The number of servers to build (mutually exclusive with `exact_count:`
| `count_group:` | N | | | Required when `exact_count:` is specified.  The Server Group use to determine how many severs to deploy.
| `cpu:` | N | 1 | | How many CPUs to provision on the server |
| `cpu_autoscale_policy_id:` | N | | | The autoscale policy to assign to the server.
| `custom_fields:` | N | | | A dictionary of custom fields to set on the server.
| `description:` | N | Set to `name:` if not provided | | The description to set for the server |
| `exact_count:` | N | | | Run in *idempotent* mode.  Will insure that this exact number of servers are running in the provided group, creating and deleting them to reach that count.  Requires `count_group:` to be set.
| `group:` | N | 'Default Group' | | The Server Group to create servers under.  |
| `ip_address:` | N | Provided by the platform it not set | | The IP Address for the server. One is assigned if not provided. 
| `location:` | N | Defaults to the default datacenter for the account | | The Datacenter to create servers in.
| `managed_os:` | N | N | | Whether to create the server as 'Managed' or not.
| `memory:` | N | 1 | Any valid int value | Memory in GB.
| `name:` | Y | | | A 1 - 6 character identifier to use for the server.
| `network_id:` | N | The first vlan in the datacenter under that account | | The text vlan identifier on which to create the servers.  Defaults if not provided.
| `packages:` | N | | | Blueprints to run on the created server.  Make reference to the Blueprint ID and not the name.|
| `password:` | N | Generated if not provided | | Password for the administrator user.  This password must be at least 3 of the 4 standard items.  Upper case, Lower Case, Numbers, and Special Characters (Some special characters may have issues.  This needs to be tested.)
| `primary_dns:` | N | Provided by the platform if not included. | | Primary DNS used by the server. |
| `secondary_dns:` | N | Provided by the platform if not included. | | Secondary DNS used by the server. |
| `server_ids:` | Y (for some states)|  |  | Required for `started`, `stopped`, and `absent` states.   A list of server Ids to insure are started, stopped, or absent.
| `source_server_password:` | N | | | The password for the source server if a clone is specified |
| `state:` | Y | | `present`, `started`, `stopped`, `absent` | The state to insure that the provided resources are in.
| `storage_type:` | N | `standard` |`standard`, `ssd` | The type of storage to attach to the server.
| `template:` | Y |  | any valid template | The template to user for server creation.  Will search for a template if a partial string is provided.  Example: `ubuntu-14-64` will build an Ubuntu 14.04 64bit server.
| `ttl:` | N | | Any valid int > 3600 | The time to live for the server.  The server will be deleted when this expires. |
| `type:` | N | `standard` | `standard`, `hyperscale`, `bareMetal`| The type of server to create.
| `configuration_id:` | N | |  | The identifier for the specific configuration type of bare metal server to deploy. |
| `os_type:` | N |  | `redHat6_64Bit`, `redHat7_64Bit`, `centOS6_64Bit`, `centOS7_64Bit`, `windows2012R2Standard_64Bit`, `ubuntu14_64Bit`, `Ubuntu16_64Bit`| The OS to provision with the bare metal server.
| `v2_api_username:` | N | | | The control portal user to use for the task.  ```This should be provided by setting environment variables instead of including it in the playbook.```
| `v2_api_passwd:` | N | | | The control portal password to use for the task.  ```This should be provided by setting environment variables instead of including it in the playbook.```
| `wait:` | N | True | Boolean| Whether to wait for the provisioning tasks to finish before returning.

## clc_modify_server Module

This module can be used to modify server configuration in CLC.

### Example Playbook
```yaml
---
- name: modify clc server example
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Modify CPU and Memory of two servers at CLC
      clc_modify_server:
        server_ids:
            - UC1ACCTSRVR01
            - UC1ACCTSRVR02
        cpu: 2
        memory: 4
        wait: True
        state: present
      register: clc
    - name: debug
      debug: var=clc.server_ids
```

```yaml
---
- name: modify clc server example
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Modify Memory of a server at CLC
      clc_modify_server:
        server_ids:
            - UC1ACCTSRVR01
        memory: 8
        wait: True
        state: present
      register: clc
    - name: debug
      debug: var=clc.server_ids
```

```yaml
---
- name: modify clc server example
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Modify anti affinity policy of a hyper scale server at CLC
      clc_modify_server:
        server_ids:
            - UC1ACCTSRVR01
        anti_affinity_policy_name: 'aa_policy'
        wait: True
        state: present
      register: clc
    - name: debug
      debug: var=clc.server_ids
```

```yaml
---
- name: modify clc server example
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: add alert policy of a server at CLC
      clc_modify_server:
        server_ids:
            - UC1ACCTSRVR01
        alert_policy_name: 'alert_policy'
        state: present
```

```yaml
---
- name: modify clc server example - add nic
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: add secondary nic
      clc_modify_server:
        server_ids:
            - UC1ACCTSRVR01
        additional_network: '613a25aff2124d10a71b16cd6fb28975'
```

### Available Parameters

| Parameter | Required | Default | Choices | Description |
|-----------|:--------:|:-------:|:-------:|-------------|
| `server_ids:` | Y |  |  | The lis of servers to be modified.
| `cpu:` | N |  | valid int value | How many CPUs to set on the server.
| `memory:` | N |  | valid int value | Memory in GB.
| `additional_network:` | N |  | ID or Name of network for an additional nic to be added.
| `anti_affinity_policy_id:` | N | | | The anti-affinity policy id to assign to the server. This is mutually exclusive with `anti_affinity_policy_name:`
| `anti_affinity_policy_name:` | N | | | The anti-affinity policy name to assign to the server. This is mutually exclusive with `anti_affinity_policy_id:`
| `alert_policy_id:` | N | | | The alert policy id to assign to the server. This is mutually exclusive with `alert_policy_name:`
| `alert_policy_name:` | N | | | The alert policy name to assign to the server. This is mutually exclusive with `alert_policy_id:`
| `state:` | Y | `present` | `present` | The state to insure that the provided resources are in. `absent` state is not supported for cpu and memory parameters
| `v2_api_username:` | N | | | The control portal user to use for the task.  ```This should be provided by setting environment variables instead of including it in the playbook.```
| `v2_api_passwd:` | N | | | The control portal password to use for the task.  ```This should be provided by setting environment variables instead of including it in the playbook.```
| `wait:` | N | True | Boolean| Whether to wait for the provisioning tasks to finish before returning.

## clc_server_fact Module
Retrieve facts about servers in Centurylink Cloud.

### Example Playbook
```yaml
- name: Retrieve Server Facts
  clc_server_fact:
    server_id: UC1ACCTSRVR10
```

```yaml
- name: Retrieve Server Facts With Credentials
  clc_server_fact:
    server_id: UC1ACCTSRVR10
    credentials: true
```
### Available Parameters

| Parameter | Required | Default | Choices | Description |
|-----------|:--------:|:-------:|:-------:|-------------|
| `server_id` | Y | | | The server id to retrieve facts for.
| `credentials` | N | False | False, True | Indicates if the server credentials should be returned in the facts.

## clc_group Module

Create or deletes Server Groups at CenturyLink Cloud.

### Example Playbook
```yaml
---
- name: Create Server Group
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create / Verify a Server Group at CenturyLink Cloud
      clc_group:
        name: 'My Cool Server Group'
        parent: 'Default Group'
        state: present
      register: clc

    - name: debug
      debug: var=clc
```

```yaml
---
- name: Delete Server Group
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Delete / Verify Absent a Server Group at CenturyLink Cloud
      clc_group:
        name: 'My Cool Server Group'
        parent: 'Default Group'
        state: absent
      register: clc

    - name: debug
      debug: var=clc
```

### Available Parameters

| Parameter | Required | Default | Choices | Description |
|-----------|:--------:|:-------:|:-------:|-------------|
| `name:` | Y | | | The Name of the Server Group |
| `description:` | N | none | | A description of the Server Group
| `parent:` | N |top level	 | | The parent group of the server group
| `location:` | N |the default datcenter associated with the account | | Datacenter to create the group in
| `state:` | N | present|present, absent | Whether to create or delete the group

## clc_group_fact Module
Retrieve facts about groups in Centurylink Cloud.

### Example Playbook
```yaml
---
- name: Retrieve Group Facts
  clc_group_fact:
    group_id: 31d13f501459411ba59304f3d47486eb
```

### Available Parameters
| Parameter | Required | Default | Choices | Description |
|-----------|:--------:|:-------:|:-------:|-------------|
| `group_id` | Y | | | The group id to retrieve facts for.

## clc_aa_policy Module

Create or deletes Anti Affinity Policies at CenturyLink Cloud.

### Example Playbook
```yaml
---
- name: Create AA Policy
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create an Anti Affinity Policy
      clc_aa_policy:
        name: 'Hammer Time'
        location: 'UK3'
        state: present
      register: policy

    - name: debug
      debug: var=policy
```

```yaml
---
- name: Delete AA Policy
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Delete an Anti Affinity Policy
      clc_aa_policy:
        name: 'Hammer Time'
        location: 'UK3'
        state: absent
      register: policy

    - name: debug
      debug: var=policy
```

### Available Parameters

| Parameter | Required | Default | Choices | Description |
|-----------|:--------:|:-------:|:-------:|-------------|
| `name:` | Y | | | The Name of the Anti Affinity Policy |
| `location:` | Y | | | Datacenter in which the policy lives/should live |
| `state:` | N | present | present, absent | Whether to create or delete the policy |

## clc_publicip Module
Creates a public ip on an existing server or servers.

### Example Playbook
```yaml
---
- name: Add Public IP to Server
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create Public IP For Servers
      clc_publicip:
        protocol: 'TCP'
        ports:
            - 80
        server_ids:
            - UC1ACCTSRVR01
            - UC1ACCTSRVR02
        source_restrictions:
            - 1.1.1.0/24
            - 2.2.2.0/32
        state: present
      register: clc

    - name: debug
      debug: var=clc
```

```yaml
---
- name: Delete Public IP from Server
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create Public IP For Servers
      clc_publicip:
        server_ids:
            - UC1ACCTSRVR01
            - UC1ACCTSRVR02
        state: absent
      register: clc

    - name: debug
      debug: var=clc
```
### Available Parameters

| Parameter | Required | Default | Choices | Description |
|-----------|:--------:|:-------:|:-------:|-------------|
| `protocol:` | N |TCP | | The Protocol that the public IP will listen for |
| `ports:` | Y | | | A list of ports to expose|
| `server_ids:` | Y |  |  | A list of servers to create public ips on. |
| `source_restrictions:` | N |  |  | A list of IP range allowed to access the public IP which is specified using CIDR notation. |
| `state:` | N | `present` | `present`,`absent` | Determine whether to create or delete public IPs.  If `present` module will not create a second public ip if one already exists. |
| `wait:` | N | True | Boolean| Whether to wait for the tasks to finish before returning. |

## clc_server_snapshot Module
Create/Delete/Restore a snapshot on an existing server or servers.

### Example Playbook
```yaml
---
- name: Create a snapshot on a set of servers
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create server snapshot
      clc_server_snapshot:
        server_ids:
            - UC1ACCTSRVR01
            - UC1ACCTSRVR02
        expiration_days: 1
        wait: True
        state: present
```

```yaml
---
- name: Restore a snapshot on a set of servers
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Restore server snapshot
      clc_server_snapshot:
        server_ids:
            - UC1ACCTSRVR01
            - UC1ACCTSRVR02
        wait: True
        state: restore
```

```yaml
---
- name: Delete a snapshot on a set of servers
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Delete server snapshot
      clc_server_snapshot:
        server_ids:
            - UC1ACCTSRVR01
            - UC1ACCTSRVR02
        wait: True
        state: absent
```

### Available Parameters

| Parameter | Required | Default | Choices | Description |
|-----------|:--------:|:-------:|:-------:|-------------|
| `server_ids:` | Y |  |  | A list of servers to create public ips on. |
| `expiration_days:` | N | `7` |  | Take a Hypervisor level snapshot retained for between 1 and 10 days (7 is default). Currently only one snapshop may exist at a time, thus will delete snapshots if one already exists before taking this snapshot. |
| `state:` | N | `present` | `present`,`absent`,`restore` | Determine whether to create or delete or restore snapshots.  If `present` module will not create a second snapshot if one already exists. |
| `wait:` | N | True | Boolean| Whether to wait for the tasks to finish before returning. |

## clc_blueprint_package Module
Executes a blue print package on existing set of servers.

### Example Playbook
```yaml
---
- name: Install a blue print package on set of servers
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create server snapshot
      clc_blueprint_package:
        server_ids:
            - UC1ACCTSRVR01
            - UC1ACCTSRVR02
        package_id: 77abb844-579d-478d-3955-c69ab4a7ba1a
        package_params: {}
```

### Available Parameters

| Parameter | Required | Default | Choices | Description |
|-----------|:--------:|:-------:|:-------:|-------------|
| `server_ids:` | Y |  |  | A list of servers to deploy blue print package on. |
| `package_id:` | Y |  |  | The package id which needs to be deployed |
| `package_params:` | N | {} |  | The arguments required for the package execution.|
| `state:` | N | `present` | `present` | If `present` module will deploy the package. |
| `wait:` | N | True | Boolean| Whether to wait for the tasks to finish before returning. |
| `ignore_failures` | N | False | Boolean | A flag indicating if the failures to be ignored if any of the servers in the list encountered a failure. |


## clc_loadbalancer Module
Create/Delete a loadbalancer

### Example Playbook
```yaml
---
- name: Create Loadbalancer
  hosts: localhost
  connection: local
  tasks:
    - name: Create Loadbalancer
      clc_loadbalancer:
        name: test3
        description: test3
        alias: WFAD
        location: WA1
        port: 443
        nodes:
          - { 'ipAddress': '10.82.152.15', 'privatePort': 80 }
          - { 'ipAddress': '10.82.152.16', 'privatePort': 80 }
        state: present
```

```yaml
---
- name: Delete LoadbalancerPool
  hosts: localhost
  connection: local
  tasks:
    - name: Delete Loadbalancer Pool
      clc_loadbalancer:
        name: test3
        description: test3
        alias: WFAD
        location: WA1
        port: 443
        state: port_absent
```

```yaml
---
- name: Add nodes to an existing loadbalancer pool
  hosts: localhost
  connection: local
  tasks:
    - name: Add nodes to pool
      clc_loadbalancer:
        name: test3
        description: test3
        alias: WFAD
        location: WA1
        port: 443
        nodes:
          - { 'ipAddress': '10.82.152.17', 'privatePort': 80 }
          - { 'ipAddress': '10.82.152.18', 'privatePort': 80 }
        state: nodes_present
```

```yaml
---
- name: Remove nodes from an existing loadbalancer pool
  hosts: localhost
  connection: local
  tasks:
    - name: Remove nodes from pool
      clc_loadbalancer:
        name: test3
        description: test3
        alias: WFAD
        location: WA1
        port: 443
        nodes:
          - { 'ipAddress': '10.82.152.17', 'privatePort': 80 }
          - { 'ipAddress': '10.82.152.18', 'privatePort': 80 }
        state: nodes_absent
```

```yaml
---
- name: Delete Loadbalancer
  hosts: localhost
  connection: local
  tasks:
    - name: Delete Loadbalanacer
      clc_loadbalancer:
        name: test3
        alias: WFAD
        location: WA1
        state: absent
```

### Available Parameters

| Parameter | Required | Default | Choices | Description |
|-----------|:--------:|:-------:|:-------:|-------------|
| `name:` | Y |  |  | The name of the loadbalancer |
| `description` | N |  |  | A description for the loadbalancer |
| `alias` | Y |  |  | Your CLC Account Alias |
| `location` | Y |  |  | The datacenter your loadbalancer resides in |
| `port` | N |  | 80, 443 | The port for your loadbalancer pool |
| `method` | N | roundRobin | roundRobin, sticky | The loadbalancing method you want to use |
| `persistence` | N | standard | standard, sticky | The loadbalancing persistence you want to use |
| `nodes` | N |  |  | A list of nodes you want your loadbalancer to send traffic to |
| `status` | N | enabled | enabled, disabled | The status of your loadbalancer |
| `state` | N | present | present, absent, port_absent, nodes_present, nodes_absent | Determine whether to create or delete your loadbalancer. If `present` module will not create another loadbalancer with the same name. If `absent` module will delete the entire loadbalancer. If `port_absent` module will delete the loadbalancer port and associated nodes only. If `nodes_present` module will ensure the provided nodes are added to the load balancer pool. If `nodes_absent` module will ensure the provided nodes are removed from the load balancer pool.|

## clc_alert_policy Module
Create/Update/Delete an alert policy in CLC

### Example Playbook
```yaml
---
- name: Create alert policy example
  hosts: localhost
  connection: local
  tasks:
    - name: Create alert policy on disk
      clc_alert_policy:
        alias: wfad
        name: testalert
        alert_recipients:
            - test1@centurylink.com
            - test2@centurylink.com
        metric: 'disk'
        duration: '00:05:00'
        threshold: 80
        state: present
```

```yaml
---
- name: Delete alert policy example
  hosts: localhost
  connection: local
  tasks:
    - name: Delete alert policy
      clc_alert_policy:
        alias: wfad
        name: testalert
        state: absent
      register: clc
```

### Available Parameters

| Parameter | Required | Default | Choices | Description |
|-----------|:--------:|:-------:|:-------:|-------------|
| `name:` | N |  |  | The name of the alert policy. This is mutually exclusive with `id`. this is required with state is `present` |
| `id` | N |  |  | The alert policy id. This is mutually exclusive with `name`. |
| `alias` | Y |  |  | The CLC Account Alias |
| `alert_recipients` | N |  |  | A list of email ids to send alert notification. This is required when state is `present` |
| `metric` | N |  | `cpu`, `memory`, `disk` | The metric on which to measure the condition that will trigger the alert. This is required when state is `present` |
| `duration` | N |  |  | The length of time in minutes that the condition must exceed the threshold. This is required when state is `present` |
| `threshold` | N |  |  | The threshold that will trigger the alert when the metric equals or exceeds it. This number represents a percentage and must be a value between 5.0 - 95.0 that is a multiple of 5.0. This is required when state is `present` |
| `state` | N | `present` | `present`, `absent` | Determine whether to create or delete alert policy. If `present` module will not create another alert policy with the same name. If `absent` module will delete the alert policy.|

## clc_firewall_policy Module
Create/Delete a Firewall Policy

### Example Playbook

```yaml
---
- name: Create Firewall Policy
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create / Verify an Firewall Policy at CenturyLink Cloud
      clc_firewall_policy:
        source_account_alias: WFAD
        location: VA1
        state: present
        source: ['10.128.216.0/24']
        destination: [10.128.216.0/24']
        ports: ['any']
        destination_account_alias: WFAD
```

```yaml
---
- name: Delete Firewall Policy
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Delete an Firewall Policy at CenturyLink Cloud
      clc_firewall_policy:
        source_account_alias: WFAD
        location: VA1
        state: absent
        firewall_policy_id: 'c62105233d7a4231bd2e91b9c791eaae'
```

### Available Parameters

| Parameter | Required | Default | Choices | Description |
|-----------|:--------:|:-------:|:-------:|-------------|
| `location` | Y |  |  | Target datacenter for the firewall policy |
| `ports` | N |  | any, icmp, TCP/123, UDP/123, TCP/123-456, UDP/123-456'| types of ports associated with the policy. TCP & UDP can take in single ports or port ranges. |
| `source` | For Create |  |  | Source addresses for traffic on the originating firewall |
| `destination` | For Create |  |  | Destination addresses for traffic on the terminating firewall |
| `source_account_alias` | Y |  |  | CLC alias for the source account |
| `destination_account_alias` | N |  |  | CLC alias for the destination account |
| `firewall_policy_id` | N |  |  | Id of the firewall policy |
| `wait` | N |  True  |  True, False | Whether to wait for the provisioning tasks to finish before returning. |
| `state` | Y | present | present, absent | Whether to create or delete the firewall policy
| `enabled` | N | True | True, False | If the firewall policy is enabled or disabled



## clc_network Module

Create or delete Network at CenturyLink Cloud.

### Example Playbook
```yaml
---
- name: Create Network
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create and update a new network
      clc_network:
        location: 'ut1'
        state: present
        name: 'ProdNet5000'
        description: 'Production Minecraft'
      register: net

    - debug: var=net
```

```yaml
---
- name: Delete Network
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Delete-ification
      clc_network:
        location: 'ut1'
        state: absent
        id: 'vlan_1306_10.81.206'
      register: net

    - debug: var=net

```

### Available Parameters

| Parameter | Required | Default | Choices | Description |
|-----------|:--------:|:-------:|:-------:|-------------|
| `description` | N | | | Description for the network |
| `id` | N | | | Identifier for network to be updated/deleted.  This is required when state is 'absent'.  This is used to find an existing network when state is 'present' and takes precedence over `name`.  The `id` field can be the network id, network name, or network vlan. |
| `location` | Y | | | Datacenter in which the network lives |
| `name` | N | | | The Name of the network.  This is used to find an existing network when state is 'present'; if not found, the claimed network is given this name. |
| `state` | N | present | present, absent | Whether to claim or release the network |
| `wait` | N | True | True, False | Whether to wait for network create to complete |


## <a id="dyn_inventory"></a>Dynamic Inventory Script

Scans all datacenters and returns an inventory of servers and server groups to Ansible.  This script returns all information about hosts in the inventory _meta dictionary.

The following information is returned for each host:

| hostvar | Description |
|---------| :-----------:|
| `ansible_ssh_host` | Set to the first internal ip address|
| `clc_custom_fields` | A dictionary of custom fields set on the server in the Control Portal|
| `clc_data` | A dictionary of all the data returned by the API|

### Usage
Command Line:
```bash
ansible all -i inventory/clc_inv.py -m ping
```

Access the CLC hostvars from a play defined in yaml:

```yaml
---
- name: Read Hostvars for Servers
  hosts: all
  gather_facts: False
  tasks:
    - name: Print PowerState returned by Dynamic Inventory / CLC API
      debug: msg="PowerState={{ hostvars[inventory_hostname]['clc_data']['details']['powerState'] }}"
```

---
## Working with the source code
Our recommended approach to working with the clc-ansible-module code base is to create a virtual environment and working with the code from within that environment.  The steps below outline the actiions necessary to get a functional development environment up and running.

### Create a virtual environment
- move to your normal development space on your system.  We will be creating our virtual environment in this location.
- Execute:`
`virtualenv clc-ansible-module`
`
- Make the virutual environment active:`
`. ./clc-ansible-module/bin/activate`
`

### Install necessary dependencies
- `pip install -r requirements.txt`

### Last minute updates to your environment
Update your active PATH with reference some binaries we just installed.

  `export PATH='pwd'/clc-ansible-module/bin:$PATH`

### Get the project
```bash
cd clc-ansible-module
mkdir workspace
cd workspace
git clone https://github.com/CenturyLinkCloud/clc-ansible-module.git
cd clc-ansible-module
```

### Build the project
```bash
python ./setup.py build
python ./setup.py install
```
- This step isn't required to build the module set.  It's primarily used to help the Runner team manage changes and releases.

### Submitting Changes
##### PR's are welcome!

Please create an Issue in Github against the project prior to doing any custom work or submitting a PR.

All changes must be submitted as PR's against the Develop branch (Github Pull Requests). - 
`git checkout develop`

Please create one PR for each change.  Please keep the change small and specific.  


 	
