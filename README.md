# clc-ansible-module

These are additional, unofficial Ansible modules for managing CenturyLink Cloud.

To use this, add this directory to to the ANSIBLE_LIBRARY environment variable, or symlink this directory to ./library in the directory of the playbook that uses it.

## Authentication

In order to use these playbooks, you must set the following environment variables:

```
export CLC_V2_API_USERNAME = <your Control Portal Username>
export CLC_V2_API_PASSWD = <your Control Portal Password>
```

You can also set them as parameters on the tasks themselves, though I wouldn't recommend it.  The modules only use the V2 API at this point.  There are hooks in the code to set a V1 key and password if they're provided, but they are never used.


## clc-server Module

Create, delete, start, or stop a server at CLC.  This module can be run in two modes: **idempotent** and **non-idempotent**. The module is idempotent if you specify the *exact_count* and *count_group* parameters.  In that case, it will create or delete the right number of servers to make sure that the *count_group* server group match the specified *exact_count* param.  

If you just specify *count* instead of *exact_count*, it is in non-idempotent mode and will create *count* number of servers every time it's run.

###Example Playbook
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

###Available Parameters

| Parameter | Required | Default | Choices | Description |
|-----------|:--------:|:-------:|:-------:|-------------|
| `additional_disks:` | N | | | Specify additional disks for the server
| `v2_api_username:` | N | | | The control portal user to use for the task.  ```This should be provided by setting environment variables instead of including it in the playbook.```
| `v2_api_passwd:` | N | | | The control portal password to use for the task.  ```This should be provided by setting environment variables instead of including it in the playbook.```




## clc-auth-key Module

## Dynamic Inventory Module