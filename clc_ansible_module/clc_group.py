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
    - requests >= 2.5.0
    - clc-sdk
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

from distutils.version import LooseVersion

try:
    import requests
except ImportError:
    REQUESTS_FOUND = False
else:
    REQUESTS_FOUND = True

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


class ClcGroup(object):

    clc = None
    root_group = None

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
        if not REQUESTS_FOUND:
            self.module.fail_json(
                msg='requests library is required for this module')
        if requests.__version__ and LooseVersion(requests.__version__) < LooseVersion('2.5.0'):
            self.module.fail_json(
                msg='requests library  version should be >= 2.5.0')
        self._headers = {'Content-Type': 'application/json'}
        self._set_user_agent()

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

        self._set_clc_credentials_from_env()
        self.group_dict = self._get_group_tree_for_datacenter(
            datacenter=location)

        if state == "absent":
            changed, group, requests_lst = self._ensure_group_is_absent(
                group_name=group_name, parent_name=parent_name)
            if requests_lst:
                self._wait_for_requests_to_complete(requests_lst)
        else:
            changed, group = self._ensure_group_is_present(
                group_name=group_name, parent_name=parent_name, group_description=group_description)
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

    def _set_clc_credentials_from_env(self):
        """
        Set the CLC Credentials on the sdk by reading environment variables
        :return: none
        """
        env = os.environ
        v2_api_token = env.get('CLC_V2_API_TOKEN', False)
        v2_api_username = env.get('CLC_V2_API_USERNAME', False)
        v2_api_passwd = env.get('CLC_V2_API_PASSWD', False)
        clc_alias = env.get('CLC_ACCT_ALIAS', False)
        self.api_url = env.get('CLC_V2_API_URL', 'https://api.ctl.io')

        if v2_api_token and clc_alias:
            self.v2_api_token = v2_api_token
            self.clc_alias = clc_alias
        elif v2_api_username and v2_api_passwd:
            try:
                response = open_url(
                    url=self.api_url + '/v2/authentication/login',
                    method='POST',
                    headers=self._headers,
                    data=json.dumps({'username': v2_api_username,
                                     'password': v2_api_passwd}))
            # TODO: Handle different response codes from API
            except urllib2.HTTPError as ex:
                return self.module.fail_json(msg=ex)
            if response.code not in [200]:
                return self.module.fail_json(
                    msg='Failed to authenticate with clc V2 api.')

            r = json.loads(response.read())
            self.v2_api_token = r['bearerToken']
            self.clc_alias = r['accountAlias']
            self.clc_location = r['locationAlias']
        else:
            return self.module.fail_json(
                msg="You must set the CLC_V2_API_USERNAME and CLC_V2_API_PASSWD "
                    "environment variables")

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

        if self._group_exists(group_name=group_name, parent_name=parent_name):
            if not self.module.check_mode:
                group.append(group_name)
                result = self._delete_group(group_name)
                results.append(result)
            changed = True
        return changed, group, results

    def _delete_group(self, group_name):
        """
        Delete the provided server group
        :param group_name: string - the server group to delete
        :return: none
        """
        response = None
        group, parent = self.group_dict.get(group_name)
        try:
            response = group.Delete()
        except CLCException as ex:
            self.module.fail_json(msg='Failed to delete group :{0}. {1}'.format(
                group_name, ex.response_text
            ))
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
        parent = parent_name if parent_name is not None else self.root_group.name
        description = group_description
        changed = False
        group = group_name

        parent_exists = self._group_exists(group_name=parent, parent_name=None)
        child_exists = self._group_exists(
            group_name=group_name,
            parent_name=parent)

        if parent_exists and child_exists:
            group, parent = self.group_dict[group_name]
            changed = False
        elif parent_exists and not child_exists:
            if not self.module.check_mode:
                group = self._create_group(
                    group=group,
                    parent=parent,
                    description=description)
            changed = True
        else:
            self.module.fail_json(
                msg="parent group: " +
                parent +
                " does not exist")

        return changed, group

    def _create_group(self, group, parent, description):
        """
        Create the provided server group
        :param group: clc_sdk.Group - the group to create
        :param parent: clc_sdk.Parent - the parent group for {group}
        :param description: string - a text description of the group
        :return: clc_sdk.Group - the created group
        """
        response = None
        (parent, grandparent) = self.group_dict[parent]
        try:
            response = parent.Create(name=group, description=description)
        except CLCException as ex:
            self.module.fail_json(msg='Failed to create group :{0}. {1}'.format(
                group, ex.response_text))
        return response

    def _group_exists(self, group_name, parent_name):
        """
        Check to see if a group exists
        :param group_name: string - the group to check
        :param parent_name: string - the parent of group_name
        :return: boolean - whether the group exists
        """
        result = False
        if group_name in self.group_dict:
            (group, parent) = self.group_dict[group_name]
            if parent_name is None or parent_name == parent.name:
                result = True
        return result

    def _get_group_tree_for_datacenter(self, datacenter=None):
        """
        Walk the tree of groups for a datacenter
        :param datacenter: string - the datacenter to walk (ex: 'UC1')
        :return: a dictionary of groups and parents
        """
        if datacenter is None:
            datacenter = self.clc_location
        # TODO: Remove clc_sdk dependency
        try:
            headers = {'Authorization': 'Bearer {0}'.format(
                self.v2_api_token)}
            headers.update(self._headers)
            response = open_url(
                url='{0}/v2/datacenters/{1}/{2}'.format(
                    self.api_url, self.clc_alias, datacenter),
                method='GET',
                headers=headers,
                data={'GroupLinks': 'true'})
        # TODO: Handle different response codes from API
        except urllib2.HTTPError as ex:
            return self.module.fail_json(msg=ex)
        #if response.code not in [200]:
        #    return self.module.fail_json(
        #        msg='Failed to authenticate with clc V2 api.')

        r = json.loads(response.read())
        root_group_id, root_group_name = [(obj['id'], obj['name'])
                                          for obj in r['links']
                                          if obj['rel'] == "group"][0]

        try:
            headers = {'Authorization': 'Bearer {0}'.format(
                self.v2_api_token)}
            headers.update(self._headers)
            response = open_url(
                url='{0}/v2/groups/{1}/{2}'.format(
                    self.api_url, self.clc_alias, root_group_id),
                method='GET',
                headers=headers)
        # TODO: Handle different response codes from API
        except urllib2.HTTPError as ex:
            return self.module.fail_json(msg=ex)

        self.group_data = json.loads(response.read())
        # TODO: Replicate functionality of Group.Subgroups()
        # Basically iterate through all the groups and save off the info
        # Need to figure out expected data structure


        self.root_group = self.clc.v2.Datacenter(
            location=datacenter).RootGroup()
        return self._walk_groups_recursive(
            parent_group=None,
            child_group=self.root_group)

    def _walk_groups_recursive(self, parent_group, group_data):
        """
        Walk a parent-child tree of groups, starting with the provided child group
        :param parent_group: clc_sdk.Group - the parent group to start the walk
        :param child_group: clc_sdk.Group - the child group to start the walk
        :return: a dictionary of groups and parents
        """
        group = self._group_object(group_data)
        result = {group['name']: (group, parent_group)}
        for child_data in group_data['groups']:
            if child_data['type'] != 'default':
                continue
            result.update(self._walk_groups_recursive(group, child_data))
        return result

    def _group_object(self, group_data):
        """
        Construct a group object that maps JSON dictionary values to attributes
        :param group_data:
        :return: An object that contains
        """
        group = object()
        for attr in ['id', 'name', 'description', 'type']:
            setattr(group, attr, group_data[attr])
        return group

    def _wait_for_requests_to_complete(self, requests_lst):
        """
        Waits until the CLC requests are complete if the wait argument is True
        :param requests_lst: The list of CLC request objects
        :return: none
        """
        if not self.module.params['wait']:
            return
        for request in requests_lst:
            request.WaitUntilComplete()
            for request_details in request.requests:
                if request_details.Status() != 'succeeded':
                    self.module.fail_json(
                        msg='Unable to process group request')

    def _set_user_agent(self):
        # Helpful ansible open_url params
        # data, headers, http-agent
        agent_string = 'ClcAnsibleModule/' + __version__
        self._headers['Api-Client'] = agent_string
        self._headers['User-Agent'] = 'Python-urllib2/{0} {1}'.format(
            urllib2.__version__, agent_string)


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
