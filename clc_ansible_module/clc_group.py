#!/usr/bin/env python
# -*- coding: utf-8 -*-
# CenturyLink Cloud Ansible Modules.
#
# These Ansible modules enable the CenturyLink Cloud v2 API to be called
# from an within Ansible Playbook.
#
# This file is part of CenturyLink Cloud, and is maintained
# by the Workflow as a Service Team
#
# Copyright 2015 CenturyLink 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# CenturyLink Cloud: http://www.CenturyLinkCloud.com
# API Documentation: https://www.centurylinkcloud.com/api-docs/v2/
#

DOCUMENTATION = '''
module: clc_group
short_description: Create/delete Server Groups at Centurylink Cloud
description:
  - Create or delete Server Groups at Centurylink Centurylink Cloud
version_added: "2.0"
options:
  name:
    description:
      - The name of the Server Group
    required: True
  description:
    description:
      - A description of the Server Group
    required: False
  parent:
    description:
      - The parent group of the server group. If parent is not provided, it creates the group at top level.
    required: False
  location:
    description:
      - Datacenter to create the group in. If location is not provided, the group gets created in the default datacenter
        associated with the account
    required: False
  state:
    description:
      - Whether to create or delete the group
    default: present
    choices: ['present', 'absent']
  wait:
    description:
      - Whether to wait for the tasks to finish before returning.
    choices: [ True, False ]
    default: True
    required: False
requirements:
    - python = 2.7
author: "CLC Runner (@clc-runner)"
notes:
    - To use this module, it is required to set the below environment variables which enables access to the
      Centurylink Cloud
          - CLC_V2_API_USERNAME, the account login id for the centurylink cloud
          - CLC_V2_API_PASSWORD, the account password for the centurylink cloud
    - Alternatively, the module accepts the API token and account alias. The API token can be generated using the
      CLC account login and password via the HTTP api call @ https://api.ctl.io/v2/authentication/login
          - CLC_V2_API_TOKEN, the API token generated from https://api.ctl.io/v2/authentication/login
          - CLC_ACCT_ALIAS, the account alias associated with the centurylink cloud
    - Users can set CLC_V2_API_URL to specify an endpoint for pointing to a different CLC environment.
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

RETURN = '''
changed:
    description: A flag indicating if any change was made or not
    returned: success
    type: boolean
    sample: True
group:
    description: The group information
    returned: success
    type: dict
    sample:
        {
           "changeInfo":{
              "createdBy":"service.wfad",
              "createdDate":"2015-07-29T18:52:47Z",
              "modifiedBy":"service.wfad",
              "modifiedDate":"2015-07-29T18:52:47Z"
           },
           "customFields":[

           ],
           "description":"test group",
           "groups":[

           ],
           "id":"bb5f12a3c6044ae4ad0a03e73ae12cd1",
           "links":[
              {
                 "href":"/v2/groups/wfad",
                 "rel":"createGroup",
                 "verbs":[
                    "POST"
                 ]
              },
              {
                 "href":"/v2/servers/wfad",
                 "rel":"createServer",
                 "verbs":[
                    "POST"
                 ]
              },
              {
                 "href":"/v2/groups/wfad/bb5f12a3c6044ae4ad0a03e73ae12cd1",
                 "rel":"self",
                 "verbs":[
                    "GET",
                    "PATCH",
                    "DELETE"
                 ]
              },
              {
                 "href":"/v2/groups/wfad/086ac1dfe0b6411989e8d1b77c4065f0",
                 "id":"086ac1dfe0b6411989e8d1b77c4065f0",
                 "rel":"parentGroup"
              },
              {
                 "href":"/v2/groups/wfad/bb5f12a3c6044ae4ad0a03e73ae12cd1/defaults",
                 "rel":"defaults",
                 "verbs":[
                    "GET",
                    "POST"
                 ]
              },
              {
                 "href":"/v2/groups/wfad/bb5f12a3c6044ae4ad0a03e73ae12cd1/billing",
                 "rel":"billing"
              },
              {
                 "href":"/v2/groups/wfad/bb5f12a3c6044ae4ad0a03e73ae12cd1/archive",
                 "rel":"archiveGroupAction"
              },
              {
                 "href":"/v2/groups/wfad/bb5f12a3c6044ae4ad0a03e73ae12cd1/statistics",
                 "rel":"statistics"
              },
              {
                 "href":"/v2/groups/wfad/bb5f12a3c6044ae4ad0a03e73ae12cd1/upcomingScheduledActivities",
                 "rel":"upcomingScheduledActivities"
              },
              {
                 "href":"/v2/groups/wfad/bb5f12a3c6044ae4ad0a03e73ae12cd1/horizontalAutoscalePolicy",
                 "rel":"horizontalAutoscalePolicyMapping",
                 "verbs":[
                    "GET",
                    "PUT",
                    "DELETE"
                 ]
              },
              {
                 "href":"/v2/groups/wfad/bb5f12a3c6044ae4ad0a03e73ae12cd1/scheduledActivities",
                 "rel":"scheduledActivities",
                 "verbs":[
                    "GET",
                    "POST"
                 ]
              }
           ],
           "locationId":"UC1",
           "name":"test group",
           "status":"active",
           "type":"default"
        }
'''

__version__ = '${version}'

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException


class ClcGroup(object):

    root_group = None

    def __init__(self, module):
        """
        Construct module
        """
        self.clc_auth = {}
        self.module = module
        self.root_group = None

    def process_request(self):
        """
        Execute the main code path, and handle the request
        :return: none
        """
        location = self.module.params.get('location')
        group_name = self.module.params.get('name')
        parent_name = self.module.params.get('parent')
        group_description = self.module.params.get('description')
        state = self.module.params.get('state')

        # TODO: Initialize credentials from non-private method
        self.clc_auth = clc_common.authenticate(self.module)
        self.root_group = self._get_group_tree_for_datacenter(
            datacenter=location)

        if state == "absent":
            changed, group, requests_lst = self._ensure_group_is_absent(
                group_name=group_name, parent_name=parent_name)
            if requests_lst:
                self._wait_for_requests_to_complete(requests_lst)
        else:
            changed, group = self._ensure_group_is_present(
                group_name=group_name, parent_name=parent_name,
                group_description=group_description)
        try:
            group = group.data
        except AttributeError:
            group = group_name
        self.module.exit_json(changed=changed, group=group)

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            name=dict(required=True),
            description=dict(default=None),
            parent=dict(default=None),
            location=dict(default=None),
            state=dict(default='present', choices=['present', 'absent']),
            wait=dict(type='bool', default=True))

        return argument_spec

    def _ensure_group_is_absent(self, group_name, parent_name):
        """
        Ensure that group_name is absent by deleting it if necessary
        :param group_name: string - the name of the clc server group to delete
        :param parent_name: string - the name of the parent group for group_name
        :return: changed, group
        """
        changed = False
        group = []
        results = []

        if parent_name is None:
            parent_name = self.root_group.name
        if self._group_exists(group_name=group_name, parent_name=parent_name):
            if not self.module.check_mode:
                # TODO: Update self.root_group removing group if successful
                group.append(group_name)
                result = self._delete_group(group_name, parent_name)
                results.append(result)
            changed = True
        return changed, group, results

    def _delete_group(self, group_name, parent_name):
        """
        Delete the provided server group
        :param group_name: string - the server group to delete
        :return: none
        """
        response = None
        if parent_name is None:
            parent_name = self.root_group.name
        group = self._group_by_name(group_name, parent_name=parent_name)
        # TODO: Check for proper HTTP response code
        try:
            response = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'DELETE', '/groups/{0}/{1}'.format(
                    self.clc_auth['clc_alias'], group.id))
        except ClcApiException as ex:
            self.module.fail_json(msg='Failed to delete group :{0}. {1}'.format(
                group_name, ex.message))
        return response

    def _ensure_group_is_present(
            self,
            group_name,
            parent_name,
            group_description):
        """
        Checks to see if a server group exists, creates it if it doesn't.
        :param group_name: the name of the group to validate/create
        :param parent_name: the name of the parent group for group_name
        :param group_description: a short description of the server group (used when creating)
        :return: (changed, group) -
            changed:  Boolean- whether a change was made,
            group:  A clc group object for the group
        """
        assert self.root_group, "Implementation Error: Root Group not set"
        if parent_name is None:
            parent_name = self.root_group.name
        description = group_description
        group = group_name
        changed = False

        parent_exists = self._group_exists(group_name=parent_name,
                                           parent_name=None)
        child_exists = self._group_exists(group_name=group_name,
                                          parent_name=parent_name)

        if parent_exists and child_exists:
            group = self._group_by_name(group_name, parent_name=parent_name)
            changed = False
        elif parent_exists and not child_exists:
            if not self.module.check_mode:
                # TODO: Update self.root_group with new information
                group = self._create_group(
                    group_name=group_name,
                    parent_name=parent_name,
                    description=description)
            changed = True
        else:
            self.module.fail_json(
                msg='parent group: {0} does not exist'.format(parent_name))

        return changed, group

    def _create_group(self, group_name, parent_name, description):
        """
        Create the provided server group
        :param group: clc_sdk.Group - the group to create
        :param parent: clc_sdk.Parent - the parent group for {group}
        :param description: string - a text description of the group
        :return: clc_sdk.Group - the created group
        """
        group = None
        parent = self._group_by_name(parent_name)
        if not description:
            description = group_name
        # TODO: Check for proper HTTP response code
        try:
            response = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'POST', '/groups/{0}'.format(self.clc_auth['clc_alias']),
                data={'name': group_name, 'description': description,
                      'parentGroupId': parent.id})
            group_data = json.loads(response.read())
            group = clc_common.Group(group_data)
        except ClcApiException as ex:
            self.module.fail_json(msg='Failed to create group :{0}. {1}'.format(
                group_name, ex.message))
        return group

    def _group_exists(self, group_name, parent_name):
        """
        Check to see if a group exists
        :param group_name: string - the group to check
        :param parent_name: string - the parent of group_name
        :return: boolean - whether the group exists
        """
        result = False
        if parent_name:
            group = self._group_by_name(group_name, parent_name=parent_name)
        else:
            group = self._group_by_name(group_name)
        if group:
            result = True
        return result

    def _get_group_tree_for_datacenter(self, datacenter=None):
        """
        Walk the tree of groups for a datacenter
        :param datacenter: string - the datacenter to walk (ex: 'UC1')
        :return: Group object for root group containing list of children
        """
        if datacenter is None:
            datacenter = self.clc_auth['clc_location']
        response = clc_common.call_clc_api(
            self.module, self.clc_auth,
            'GET', '/datacenters/{0}/{1}'.format(
                self.clc_auth['clc_alias'], datacenter),
            data={'GroupLinks': 'true'})

        r = json.loads(response.read())
        root_group_id, root_group_name = [(obj['id'], obj['name'])
                                          for obj in r['links']
                                          if obj['rel'] == "group"][0]

        response = clc_common.call_clc_api(
            self.module, self.clc_auth,
            'GET', '/groups/{0}/{1}'.format(
                self.clc_auth['clc_alias'], root_group_id))

        group_data = json.loads(response.read())
        return self._walk_groups_recursive(None, group_data)

    def _walk_groups_recursive(self, parent_group, group_data):
        """
        Walk a parent-child tree of groups, starting with the provided child group
        :param parent_group: clc.Group - Parent of group described by group_data
        :param group_data: dict - Dict of data from JSON API return
        :return: Group object from data, containing list of children
        """
        group = clc_common.Group(group_data)
        group.parent = parent_group
        for child_data in group_data['groups']:
            if child_data['type'] != 'default':
                continue
            group.children.append(self._walk_groups_recursive(group, child_data))
        return group

    def _group_by_name(self, group_name, group=None, parent_name=None):
        """
        :param group_name: Name of group to search form
        :param group: Optional group under which to search
        :param parent_name:  Optional name of parent
        :return: Group object found, or None if no groups found.
        Will return an error if multiple groups found matching parameters.
        """
        groups = self._group_by_name_recursive(
            group_name, group=group, parent_name=parent_name)
        if len(groups) > 1:
            error_message = 'Found {0:d} groups with name: \"{1}\"'.format(
                len(groups), group_name)
            if parent_name is None:
                error_message += ' in root group \"{0}\".'.format(
                    self.root_group.name)
            else:
                error_message += ' in group: \"{0}\".'.format(parent_name)
            error_message += ' Group ids: ' + ', '.join([g.id for g in groups])
            return self.module.fail_json(msg=error_message)
        elif len(groups) == 1:
            return groups[0]
        else:
            return None

    def _group_by_name_recursive(self, group_name, group=None,
                                 parent_name=None):
        """
        :param group_name: Name of group to search for
        :param group: Optional group under which to search
        :param parent_name: Optional name of parent
        :return: List of groups found matching the described parameters
        """
        groups = []
        if group is None:
            group = self.root_group
        if group_name == group.name:
            if parent_name is None:
                groups.append(group)
            elif group.parent is not None and parent_name == group.parent.name:
                groups.append(group)
        for child_group in group.children:
            groups += self._group_by_name_recursive(group_name,
                                                    group=child_group,
                                                    parent_name=parent_name)
        return groups

    def _group_full_path(self, group, id=False, delimiter=' / '):
        """
        :param group: Group object for which to show full ancestry
        :param id: Optional flag to show group id hierarchy
        :param delimiter: Optional delimiter
        :return:
        """
        path_elements = []
        while group is not None:
            if id:
                path_elements.insert(0, group.id)
            else:
                path_elements.insert(0, group.name)
            group = group.parent
        return delimiter.join(path_elements)

    def _wait_for_requests_to_complete(self, requests_lst):
        """
        Waits until the CLC requests are complete if the wait argument is True
        :param requests_lst: The list of CLC request objects
        :return: none
        """
        if not self.module.params['wait']:
            return
        for request in requests_lst:
            request.read()
            if request.code < 200 or request.code >= 300:
                self.module.fail_json(msg='Unable to process group request')


def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
        argument_spec=ClcGroup._define_module_argument_spec(),
        supports_check_mode=True)

    clc_group = ClcGroup(module)
    clc_group.process_request()

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
if __name__ == '__main__':
    main()
