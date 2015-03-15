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


## clc-auth-key Module

## Dynamic Inventory Module