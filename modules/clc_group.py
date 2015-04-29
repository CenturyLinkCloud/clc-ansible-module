#!/usr/bin/python
DOCUMENTATION = '''
module: clc-ansible-module
short_desciption: Create/delete Server Groups at Centurylink Cloud
description:
  - Create or delete Server Groups at Centurylink Centurylink Cloud
options:
  name:
    description: 
      - The name of the Server Group
  description:
    description: 
      - A description of the Server Group
  parent:
    description: 
      - The parent group of the server group
  location:
    description: 
      - Datacenter to create the group in
  state:
    description: 
      - Whether to create or delete the group
    default: present
    choices: ['present', 'absent']  


'''

EXAMPLES = '''

# Create a Server Group

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

# Delete a Server Group

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

'''





import sys
import os
import datetime
import json
# from ansible.module_utils.basic import *
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

class ClcGroup():

    clc = None
    root_group = None

    def __init__(self, module):
        self.clc = clc_sdk
        self.module = module
        self.group_dict = {}

        if not CLC_FOUND:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')

    def do_work(self):
        p = self.module.params

        self.set_clc_credentials_from_env()
        self.group_dict = self._get_group_tree_for_datacenter(datacenter=p['location'])

        if p['state'] == "absent":
            changed, group = self._ensure_group_is_absent(p)
        else:
            changed, group = self._ensure_group_is_present(p)

        if group:
            group = group.data

        self.module.exit_json(changed=changed, group=group)

    #
    #  Functions to define the Ansible module and its arguments
    #

    @staticmethod
    def define_argument_spec():
        argument_spec = dict(
            name=dict(required=True),
            description=dict(default=None),
            parent=dict(default=None),
            location=dict(default=None),
            alias=dict(default=None),
            custom_fields=dict(type='list', default=[]),
            server_ids=dict(type='list', default=[]),
            state=dict(default='present', choices=['present', 'absent'])
            )

        return argument_spec

    #
    #   Module Behavior Functions
    #

    def set_clc_credentials_from_env(self):
        '''
        Sets CLC Credentials
        '''
        env = os.environ
        v2_api_token = env.get('CLC_V2_API_TOKEN', False)
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

    def _ensure_group_is_absent(self, p):
        '''
        Deletes a Server Group
        '''
        changed = False
        group = None
        if self._group_exists(group_name=p['name'], parent_name=p['parent']):
            self._delete_group(p)
            changed = True
        return changed, group

    def _delete_group(self, p):
        '''
        Deletes a Server Group
        '''
        group, parent = self.group_dict[p['name']]
        group.Delete()

    def _ensure_group_is_present(self, p):
        '''
        Creates a Server Group
        '''
        changed = False
        group = None
        assert self.root_group, "Implementation Error: Root Group not set"
        parent = p['parent'] if p['parent'] is not None else self.root_group.name
        group = p['name']
        description = p['description']


        parent_exists = self._group_exists(group_name=parent, parent_name=None)
        child_exists = self._group_exists(group_name=group, parent_name=parent)

        if not parent_exists:
            self.module.fail_json(msg="parent group: " + parent + " does not exist")

        if parent_exists and not child_exists:
            group = self._create_group(group=group, parent=parent, description=description)
            changed = True
        else:
            group, parent = self.group_dict[p['name']]
            changed = False

        return changed, group


    def _create_group(self, group, parent, description):
        '''
        Creates a Server Group
        '''

        (parent, grandparent) = self.group_dict[parent]
        return parent.Create(name=group, description=description)


    #
    #   Utility Functions
    #

    def _group_exists(self, group_name, parent_name):
        '''
        Check to see if a group exists
        '''
        result = False
        if group_name in self.group_dict:
                (group, parent) = self.group_dict[group_name]
        if parent_name is None or parent_name == parent.name:
            result = True
        return result

    def _get_group_tree_for_datacenter(self, datacenter=None, alias=None):
        '''
        Get a datacenter's server group tree
        '''
        self.root_group = self.clc.v2.Datacenter(location=datacenter).RootGroup()
        return self._walk_groups_recursive(parent_group=None, child_group=self.root_group)

    def _walk_groups_recursive(self, parent_group, child_group):
        result = {str(child_group): (child_group, parent_group)}
        groups = child_group.Subgroups().groups
        if len(groups) > 0:
            for group in groups:
                result.update(self._walk_groups_recursive(child_group, group))
        return result

    def _get_group(self, group_name, datacenter=None, alias=None):
        '''
        Get a specified Server Group
        '''
        result = None
        try:
            result = self.clc.v2.Datacenter(location=datacenter, alias=alias).Groups().Get(group_name)
        except CLCException, e:
            if "Group not found" not in e.message:
                self.module.fail_json(msg='error looking up group: %s' % e)
        return result

def main():
    module = AnsibleModule(
            argument_spec=ClcGroup.define_argument_spec()
        )
    clc_group = ClcGroup(module)
    clc_group.do_work()


if __name__ == '__main__':
    main()