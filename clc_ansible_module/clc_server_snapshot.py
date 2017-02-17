#!/usr/bin/env python

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
module: clc_server_snapshot
short_description: Create, Delete and Restore server snapshots in CenturyLink Cloud.
description:
  - An Ansible module to Create, Delete and Restore server snapshots in CenturyLink Cloud.
version_added: "2.0"
options:
  server_ids:
    description:
      - The list of CLC server Ids.
    required: True
  expiration_days:
    description:
      - The number of days to keep the server snapshot before it expires.
    default: 7
    required: False
  state:
    description:
      - The state to insure that the provided resources are in.
    default: 'present'
    required: False
    choices: ['present', 'absent', 'restore']
  wait:
    description:
      - Whether to wait for the provisioning tasks to finish before returning.
    default: True
    required: False
    choices: [True, False]
  ignore_failures:
    description:
      - Whether to ignore and continue with the servers if any of the server snapshot fails.
    default: False
    required: False
    choices: [True, False]
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
# Note - You must set the CLC_V2_API_USERNAME And CLC_V2_API_PASSWD Environment variables before running these examples

- name: Create server snapshot
  clc_server_snapshot:
    server_ids:
        - UC1TEST-SVR01
        - UC1TEST-SVR02
    expiration_days: 10
    wait: True
    state: present

- name: Restore server snapshot
  clc_server_snapshot:
    server_ids:
        - UC1TEST-SVR01
        - UC1TEST-SVR02
    wait: True
    state: restore

- name: Delete server snapshot
  clc_server_snapshot:
    server_ids:
        - UC1TEST-SVR01
        - UC1TEST-SVR02
    wait: True
    state: absent
'''

RETURN = '''
changed:
    description: A flag indicating if any change was made or not
    returned: success
    type: boolean
    sample: True
server_ids:
    description: The list of server ids that are changed
    returned: success
    type: list
    sample:
        [
            "UC1TEST-SVR01",
            "UC1TEST-SVR02"
        ]
'''

__version__ = '${version}'

try:  # python 3
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException


class ClcSnapshot(object):

    module = None

    def __init__(self, module):
        """
        Construct module
        """
        self.clc_auth = {}
        self.module = module

    def process_request(self):
        """
        Process the request - Main Code Path
        :return: Returns with either an exit_json or fail_json
        """
        p = self.module.params
        state = p['state']
        request_list = []
        changed = False
        changed_servers = []
        failed_servers = []

        self.clc_auth = clc_common.authenticate(self.module)
        if state == 'present':
            changed, request_list, changed_servers, failed_servers = self.ensure_server_snapshot_present()
        elif state == 'absent':
            changed, request_list, changed_servers, failed_servers = self.ensure_server_snapshot_absent()
        elif state == 'restore':
            changed, request_list, changed_servers, failed_servers = self.ensure_server_snapshot_restore()

        self._wait_for_requests_to_complete(request_list)
        return self.module.exit_json(
            changed=changed,
            server_ids=changed_servers,
            failed_server_ids=failed_servers)

    def ensure_server_snapshot_present(self):
        """
        Ensures the given set of server_ids have the snapshots created
        :return: (changed, request_list, changed_servers)
                 changed: A flag indicating whether any change was made
                 request_list: the list of clc request objects from CLC API call
                 changed_servers: The list of servers ids that are modified
        """
        p = self.module.params
        server_ids = p.get('server_ids')
        expiration_days = p.get('expiration_days')
        ignore_failures = p.get('ignore_failures')

        request_list = []
        changed_servers = []
        failed_servers = []
        changed = False
        servers = clc_common.servers_by_id(self.module, self.clc_auth,
                                           server_ids)
        for server in servers:
            if len(server.data['details']['snapshots']) > 0:
                continue
            changed = True
            if not self.module.check_mode:
                request = self._create_server_snapshot(
                    server=server, expiration_days=expiration_days,
                    ignore_failures=ignore_failures)
                if request:
                    request_list.append(request)
                    changed_servers.append(server.id)
                else:
                    failed_servers.append(server.id)
        return changed, request_list, changed_servers, failed_servers

    def _create_server_snapshot(self, server, expiration_days, ignore_failures):
        """
        Create the snapshot for the CLC server
        :param server: the CLC server object
        :param expiration_days: The number of days to keep the snapshot
        :param ignore_failures: A flag indicating if failures to be ignored
        :return: the create request object from CLC API Call
        """
        if len(server.data['details']['snapshots']) > 0:
            result = self._delete_server_snapshot(server, ignore_failures)
            self._wait_for_requests_to_complete([result])
        result = None
        try:
            result = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'POST', '/operations/{alias}/servers/createSnapshot'.format(
                    alias=self.clc_auth['clc_alias']),
                data={'snapshotExpirationDays': expiration_days,
                      'serverIds': [server.id]})
        except ClcApiException as ex:
            if ignore_failures:
                return None
            else:
                return self.module.fail_json(
                    msg='Failed to create snapshot for server: {id}. '
                        '{msg}'.format(id=server.id, msg=ex.message))

        return result

    def ensure_server_snapshot_absent(self):
        """
        Ensures the given set of server_ids have the snapshots removed
        :return: (changed, request_list, changed_servers)
                 changed: A flag indicating whether any change was made
                 request_list: the list of clc request objects from CLC API call
                 changed_servers: The list of servers ids that are modified
        """
        p = self.module.params
        server_ids = p.get('server_ids')
        ignore_failures = p.get('ignore_failures')

        request_list = []
        changed_servers = []
        failed_servers = []
        changed = False
        servers = clc_common.servers_by_id(self.module, self.clc_auth,
                                           server_ids)
        for server in servers:
            if len(server.data['details']['snapshots']) == 0:
                continue
            changed = True
            if not self.module.check_mode:
                request = self._delete_server_snapshot(server, ignore_failures)
                if request:
                    request_list.append(request)
                    changed_servers.append(server.id)
                else:
                    failed_servers.append(server.id)
        return changed, request_list, changed_servers, failed_servers

    def _delete_server_snapshot(self, server, ignore_failures):
        """
        Delete snapshot for the CLC server
        :param server: the CLC server object
        :param ignore_failures: A flag indicating if failures to be ignored
        :return: the delete snapshot request object from CLC API
        """
        snapshot = self._get_snapshot_number(server)
        result = None
        try:
            result = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'DELETE', '/servers/{alias}/{id}/snapshots/{snap}'.format(
                    alias=self.clc_auth['clc_alias'], id=server.id,
                    snap=snapshot))
        except ClcApiException as ex:
            if ignore_failures:
                return None
            else:
                return self.module.fail_json(
                    msg='Failed to delete snapshot for server: {id}. '
                        '{msg}'.format(id=server.id, msg=ex.message))
        return result

    def ensure_server_snapshot_restore(self):
        """
        Ensures the given set of server_ids have the snapshots restored
        :return: (changed, request_list, changed_servers)
                 changed: A flag indicating whether any change was made
                 request_list: the list of clc request objects from CLC API call
                 changed_servers: The list of servers ids that are modified
        """
        p = self.module.params
        server_ids = p.get('server_ids')
        ignore_failures = p.get('ignore_failures')

        request_list = []
        changed_servers = []
        failed_servers = []
        changed = False
        servers = clc_common.servers_by_id(self.module, self.clc_auth,
                                           server_ids)
        for server in servers:
            if len(server.data['details']['snapshots']) == 0:
                continue
            changed = True
            if not self.module.check_mode:
                request = self._restore_server_snapshot(server, ignore_failures)
                if request:
                    request_list.append(request)
                    changed_servers.append(server.id)
                else:
                    failed_servers.append(server.id)
        return changed, request_list, changed_servers, failed_servers

    def _restore_server_snapshot(self, server, ignore_failures):
        """
        Restore snapshot for the CLC server
        :param server: the CLC server object
        :param ignore_failures: A flag indicating if failures to be ignored
        :return: the restore snapshot request object from CLC API
        """
        snapshot = self._get_snapshot_number(server)
        result = None
        try:
            result = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'POST', '/servers/{alias}/{id}/snapshots/{snap}/restore'.format(
                    alias=self.clc_auth['clc_alias'], id=server.id,
                    snap=snapshot))
        except ClcApiException as ex:
            if ignore_failures:
                return None
            else:
                return self.module.fail_json(
                    msg='Failed to restore snapshot for server: {id}. '
                        '{msg}'.format(id=server.id, msg=ex.message))
        return result

    @staticmethod
    def _get_snapshot_number(server):
        snapshot = None
        snapshots = server.data['details']['snapshots']
        if len(snapshots) > 0:
            url = [l['href'] for l in snapshots[0]['links']
                   if l['rel'] == 'self'][0]
            path_list = os.path.split(urlparse(url).path)
            snapshot = path_list[-1]
        return snapshot

    def _wait_for_requests_to_complete(self, request_list, ensure_wait=False):
        """
        Block until server snapshot requests are completed.
        :param request_list: a list of CLC API JSON responses
        :return: none
        """
        if ensure_wait or self.module.params.get('wait'):
            failed_requests_count = clc_common.wait_on_completed_operations(
                self.module, self.clc_auth,
                clc_common.operation_id_list(request_list))

            if failed_requests_count > 0:
                self.module.fail_json(
                    msg='Unable to process server snapshot request')

    @staticmethod
    def define_argument_spec():
        """
        This function defines the dictionary object required for
        package module
        :return: the package dictionary object
        """
        argument_spec = dict(
            server_ids=dict(type='list', required=True),
            expiration_days=dict(type='int', default=7),
            wait=dict(type='bool', default=True),
            ignore_failures=dict(type='bool', default=False),
            state=dict(
                type='str', default='present',
                choices=[
                    'present',
                    'absent',
                    'restore']),
        )
        return argument_spec


def main():
    """
    Main function
    :return: None
    """
    module = AnsibleModule(
        argument_spec=ClcSnapshot.define_argument_spec(),
        supports_check_mode=True
    )
    clc_snapshot = ClcSnapshot(module)
    clc_snapshot.process_request()

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
