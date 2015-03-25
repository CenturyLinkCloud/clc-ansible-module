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
    from clc import CLCException
except ImportError:
    clc_found = False
    clc_sdk = None
else:
    clc_found = True

class ClcGroup():

    def __init__(self, module):
        self.clc = clc_sdk
        self.module = module
        self.group_dict = {}


    def do_work(self):
        p = self.module.params

        if not clc_found:
            self.module.fail_json(msg='clc-python-sdk required for this module')

        self._clc_set_credentials()
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

    def _clc_set_credentials(self):
            e = os.environ

            v2_api_passwd = None
            v2_api_username = None

            try:
                v2_api_username = e['CLC_V2_API_USERNAME']
                v2_api_passwd = e['CLC_V2_API_PASSWD']
            except KeyError, e:
                self.module.fail_json(msg = "you must set the CLC_V2_API_USERNAME and CLC_V2_API_PASSWD environment variables")

            self.clc.v2.SetCredentials(api_username=v2_api_username, api_passwd=v2_api_passwd)


    def _ensure_group_is_absent(self, p):
        changed = False
        group = None

        if self._group_exists(group_name=p['name'], parent_name=p['parent']):
            self._delete_group(p)
            changed = True
        return changed, group

    def _delete_group(self, p):
        group, parent = self.group_dict[p['name']]
        group.Delete()

    def _ensure_group_is_present(self, p):
        changed = False
        group = None

        parent_exists = self._group_exists(group_name=p['parent'], parent_name=None)
        child_exists = self._group_exists(group_name=p['name'], parent_name=p['parent'])

        if not parent_exists:
            self.module.fail_json(msg="parent group: " + p['parent'] + " does not exist")

        if parent_exists and not child_exists:
            group = self._create_group(p)
            changed = True
        else:
            group, parent = self.group_dict[p['name']]
            changed = False

        return changed, group


    def _create_group(self, p):

        (parent, grandparent) = self.group_dict[p['parent']]
        return parent.Create(name=p['name'], description=p['description'])


    #
    #   Utility Functions
    #

    def _group_exists(self, group_name, parent_name):
        result = False
        if group_name in self.group_dict:
            (group, parent) = self.group_dict[group_name]

            if parent_name == parent.name or not parent_name:
                result = True

        return result



    def _group_exists(self, group_name, parent_name):
        result = False
        if group_name in self.group_dict:
            group, parent = self.group_dict[group_name]

            if parent_name == parent.name or not parent_name:
                result = True

        return result

    def _get_group_tree_for_datacenter(self, datacenter=None, alias=None):
        root_group = self.clc.v2.Datacenter(location=datacenter).RootGroup()
        return self._walk_group_tree(parent_group=None, child_group=root_group)

    def _walk_group_tree(self, parent_group, child_group):
        result = {str(child_group): (child_group, parent_group)}
        groups = child_group.Subgroups().groups
        if len(groups) > 0:
            for group in groups:
                result.update(self._walk_group_tree(child_group, group))
        return result


    def _get_group(self, module, group_name, datacenter=None, alias=None):
        result = None
        try:
            result = self.clc.v2.Datacenter(location=datacenter, alias=alias).Groups().Get(group_name)
        except CLCException, e:
            if "Group not found" not in e.message:
                module.fail_json(msg='error looking up group: %s' % e)
        return result

def main():
    module = AnsibleModule(
            argument_spec=ClcGroup.define_argument_spec()
        )
    clc_group = ClcGroup(module)
    clc_group.do_work()


if __name__ == '__main__':
    main()