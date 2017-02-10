#!/usr/bin/env python
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

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException

import mock
from mock import patch
import unittest
import StringIO
import json


class TestClcCommonFunctions(unittest.TestCase):

    def setUp(self):
        self.module = mock.MagicMock()
        self.datacenter = mock.MagicMock()

    def test_authenticate_w_creds(self):
        test_clc_auth = {
            'v2_api_url': 'https://api.ctl.io/v2/',
            'v2_api_token': 'mock_token',
            'clc_alias': 'mock_alias',
            'clc_location': 'mock_location',
        }
        auth_return = {
            'bearerToken': test_clc_auth['v2_api_token'],
            'accountAlias': test_clc_auth['clc_alias'],
            'locationAlias': test_clc_auth['clc_location']
        }
        with patch.object(clc_common, 'call_clc_api') as mock_method:
            mock_method.return_value = auth_return
            with patch.dict('os.environ',
                            {'CLC_V2_API_USERNAME': 'dummy_username',
                             'CLC_V2_API_PASSWD': 'dummy_passwd'},
                            clear=True):
                clc_common.authenticate(self.module)
        # Should fail with an HTTP error code of 400 for bad user/passwd
        # TODO: Set up better mock to fully test response from API
        mock_method.assert_called_with(
            self.module, test_clc_auth,
            'POST', '/authentication/login',
            data={'username': 'dummy_username', 'password': 'dummy_passwd'})

    def test_authenticate_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            clc_common.authenticate(self.module)
        self.assertEqual(self.module.fail_json.called, True)

    @patch.object(clc_common, 'call_clc_api')
    def test_override_v2_api_url_from_environment(self, mock_call_api):
        original_url = 'https://api.ctl.io/v2/'
        clc_auth = clc_common.authenticate(self.module)
        self.assertEqual(clc_auth['v2_api_url'], original_url)
        with patch.dict('os.environ',
                        {'CLC_V2_API_URL': 'https://unittest.example.com/',
                         'CLC_V2_API_TOKEN': 'dummy_token',
                         'CLC_ACCT_ALIAS': 'dummy_alias',
                         'CLC_LOCATION': 'dummy_location'},
                        clear=True):
            clc_auth = clc_common.authenticate(self.module)
        self.assertEqual(clc_auth['v2_api_url'], 'https://unittest.example.com/')

    def test_set_user_agent(self):
        headers = clc_common._default_headers()
        self.assertIn('ClcAnsibleModule', headers['Api-Client'])
        self.assertIn('ClcAnsibleModule', headers['User-Agent'])

    def test_walk_groups(self):
        group_data = {'name': 'Mock Group', 'id': 'mock_id',
                      'type': 'mock_type', 'groups': []}
        grp1 = mock.MagicMock()
        grp1.type = 'default'
        grp1.children = []
        res = clc_common._walk_groups(grp1, group_data)
        self.assertIsNotNone(res)

    @patch.object(clc_common, 'call_clc_api')
    def test_group_tree(self, mock_call):
        def call_api_side_effect(*args, **kwargs):
            if '/datacenters/' in args[3]:
                datacenter_data = {'links': [
                    {'rel': 'group', 'id': 'root_id', 'name': 'root_name'}]}
                return datacenter_data
            elif '/groups/' in args[3]:
                group_data = {'name': 'Mock Group', 'id': 'mock_id',
                              'type': 'mock_type', 'groups': []}
                return group_data

        clc_auth = {'v2_api_url': 'mock_url',
                    'v2_api_token': 'mock_token',
                    'clc_location': 'mock_location',
                    'clc_alias': 'mock_alias'}

        clc_common.call_clc_api.side_effect = call_api_side_effect

        clc_common.group_tree(self.module, clc_auth)
        self.assertEqual(clc_common.call_clc_api.call_count, 2)

    def test_find_group(self):
        mock_group = mock.MagicMock()
        mock_group.name = "MockGroup"

        mock_parent = mock.MagicMock()
        mock_parent.name = "MockParent"
        mock_parent.children = [mock_group]
        mock_group.parent = mock_parent

        mock_rootgroup = mock.MagicMock()
        mock_rootgroup.name = "MockRootGroup"
        mock_rootgroup.parent = None
        mock_rootgroup.children = [mock_parent]
        mock_parent.parent = mock_rootgroup

        self.assertEqual(
            clc_common.find_group(
                self.module, mock_rootgroup, 'MockGroup'),
            mock_group)
        self.assertEqual(
            clc_common.find_group(
                self.module, mock_rootgroup, 'MockGroup', 'MockParent'),
            mock_group)
        self.assertIsNone(
            clc_common.find_group(
                self.module, mock_rootgroup, 'MissingGroup'))
        self.assertIsNone(
            clc_common.find_group(
                self.module, mock_rootgroup, 'MockGroup', 'MissingParent'))

    @patch.object(clc_common, 'servers_by_id')
    def test_servers_in_group(self, mock_servers):
        group = mock.MagicMock()
        group.data = {
            'links': [
                {'rel': 'server', 'id': 'mock_id1'},
                {'rel': 'server', 'id': 'mock_id2'}
                ]
            }
        server1 = clc_common.Server({'id': 'mock_id1',
                                     'details': {'memoryMB': 2048,
                                                 'powerState': 'started'}})
        server2 = clc_common.Server({'id': 'mock_id2',
                                     'details': {'memoryMB': 2048,
                                                 'powerState': 'started'}})
        mock_servers.return_value = [server1, server2]

        res = clc_common.servers_in_group(self.module, {}, group)

        self.assertEqual(res, [server1, server2])

    @patch.object(clc_common, 'group_tree')
    def test_server_ids_in_datacenter(self, mock_group_tree):
        child_group = mock.MagicMock()
        child_group.data = {'links': [{'rel': 'server', 'id': 'mock_id2'}]}
        root_group = mock.MagicMock()
        root_group.data  = {'links': [{'rel': 'server', 'id': 'mock_id1'}]}
        root_group.children = [child_group]

        mock_group_tree.return_value = root_group

        servers = clc_common.server_ids_in_datacenter(self.module, {}, 'dc',
                                                      root_group=None)

        self.assertEqual(servers, ['mock_id1', 'mock_id2'])

    @patch.object(clc_common, 'networks_in_datacenter')
    def test_find_network_default(self, mock_networks_datacenter):
        # Setup
        mock_network = mock.MagicMock()
        mock_network.id = 'TestReturnVlan'
        mock_network.id = '12345678123456781234567812345678'
        datacenter = 'mock_dc'

        mock_networks_datacenter.return_value = [mock_network]

        clc_auth = {'v2_api_url': 'mock_url',
                    'v2_api_token': 'mock_token',
                    'clc_location': 'mock_location',
                    'clc_alias': 'mock_alias'}

        # Function Under Test
        result = clc_common.find_network(self.module, clc_auth, datacenter)

        # Assert Result
        self.assertEqual(result, mock_network)
        self.assertEqual(self.module.fail_json.called, False)

    @patch.object(clc_common, 'networks_in_datacenter')
    def test_find_network_by_id(self, mock_networks_datacenter):
        # Setup
        mock_network = mock.MagicMock()
        mock_network.name = 'TestReturnVlan'
        mock_network.id = '12345678123456781234567812345678'
        datacenter = 'mock_dc'

        mock_networks_datacenter.return_value = [mock_network]

        network_id_search = mock_network.id
        clc_auth = {'v2_api_url': 'mock_url',
                    'v2_api_token': 'mock_token',
                    'clc_location': 'mock_location',
                    'clc_alias': 'mock_alias'}

        # Function Under Test
        result = clc_common.find_network(self.module, clc_auth, datacenter,
                                         network_id_search=network_id_search)

        # Assert Result
        self.assertEqual(result, mock_network)
        self.assertEqual(self.module.fail_json.called, False)

    @patch.object(clc_common, 'networks_in_datacenter')
    def test_find_network_invalid_id(self, mock_networks_datacenter):
        # Setup
        mock_network = mock.MagicMock()
        mock_network.name = 'TestReturnVlan'
        mock_network.id = '12345678123456781234567812345678'
        datacenter = 'mock_dc'

        mock_networks_datacenter.return_value = [mock_network]

        network_id_search = 'mock_network_id'
        clc_auth = {'v2_api_url': 'mock_url',
                    'v2_api_token': 'mock_token',
                    'clc_location': 'mock_location',
                    'clc_alias': 'mock_alias'}

        # Function Under Test
        result = clc_common.find_network(self.module, clc_auth, datacenter,
                                         network_id_search=network_id_search)

        # Assert Result
        self.assertIsNone(result)

    @patch.object(clc_common, 'call_clc_api')
    def test_find_network_not_found(self, mock_call_api):
        # Setup
        datacenter = 'mock_dc'
        mock_call_api.side_effect = ClcApiException()

        clc_auth = {'v2_api_url': 'mock_url',
                    'v2_api_token': 'mock_token',
                    'clc_location': 'mock_location',
                    'clc_alias': 'mock_alias'}

        # Function Under Test
        clc_common.find_network(self.module, clc_auth, datacenter)

        # Assert Result
        self.assertEqual(self.module.fail_json.called, True)

    def test_check_policy_type(self):
        policy_str = clc_common._check_policy_type(self.module, 'alert')
        self.assertEqual(policy_str, 'alert')

        policy_str = clc_common._check_policy_type(self.module, 'antiAffinity')
        self.assertEqual(policy_str, 'anti affinity')

        self.assertEqual(self.module.fail_json.called, False)

    def test_check_policy_type_not_found(self):
        clc_common._check_policy_type(self.module, 'fake_policy')
        self.module.fail_json.assert_called_once_with(
            msg='Policy type: fake_policy not supported')

    @patch.object(clc_common, 'call_clc_api')
    def test_get_policies(self, mock_call_api):
        found_policies = {
            'items': [
                {'id': 'mock_id',
                 'location': 'mock_dc'}
            ]
        }
        mock_call_api.return_value = found_policies
        clc_auth = {'clc_alias': 'mock_alias'}

        policies = clc_common._get_policies(self.module, clc_auth,
                                            policy_type='alert')
        self.assertEqual(policies, found_policies['items'])

        policies = clc_common._get_policies(self.module, clc_auth,
                                            policy_type='alert',
                                            location='fake_dc')
        self.assertEqual(policies, [])

    @patch.object(clc_common, 'call_clc_api')
    def test_get_aa_policies_exception(self, mock_call_api):
        error = ClcApiException(message='Failed')
        mock_call_api.side_effect = error
        clc_auth = {'clc_alias': 'mock_alias'}

        clc_common._get_policies(self.module, clc_auth,
                                 policy_type='antiAffinity')

        self.module.fail_json.assert_called_once_with(
            msg='Unable to fetch anti affinity policies for account: '
                'mock_alias. Failed')

    @patch.object(clc_common, 'call_clc_api')
    def test_get_alert_policies_exception(self, mock_call_api):
        error = ClcApiException(message='Failed')
        mock_call_api.side_effect = error
        clc_auth = {'clc_alias': 'mock_alias'}

        clc_common._get_policies(self.module, clc_auth, policy_type='alert')

        self.module.fail_json.assert_called_once_with(
            msg='Unable to fetch alert policies for account: mock_alias. '
                'Failed')

    @patch.object(clc_common, '_get_policies')
    def test_find_policy_found(self, mock_get_policies):
        return_policies = [
            {'id': 'mock_id1', 'name': 'mock_name1'},
            {'id': 'mock_id2', 'name': 'mock_name2'}
        ]
        mock_get_policies.return_value = return_policies
        clc_auth = {'clc_alias': 'mock_alias'}

        policy = clc_common.find_policy(self.module, clc_auth, 'mock_name1',
                                        policy_type='alert')
        self.assertEqual(policy, return_policies[0])

        policy = clc_common.find_policy(self.module, clc_auth, 'mock_name2',
                                        policy_type='antiAffinity')
        self.assertEqual(policy, return_policies[1])

        policy = clc_common.find_policy(self.module, clc_auth, 'mock_id1',
                                        policy_type='antiAffinity')
        self.assertEqual(policy, return_policies[0])

        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, '_get_policies')
    def test_find_policy_duplicate(self, mock_get_policies):
        return_policies = [
            {'id': 'mock_id1', 'name': 'mock_name1'},
            {'id': 'mock_id2', 'name': 'mock_name2'},
            {'id': 'mock_id3', 'name': 'mock_name1'}
        ]
        mock_get_policies.return_value = return_policies
        clc_auth = {'clc_alias': 'mock_alias'}

        policy = clc_common.find_policy(self.module, clc_auth, 'mock_name1',
                                        policy_type='alert')
        self.module.fail_json.assert_called_once_with(
            msg='Multiple alert policies matching: mock_name1. '
                'Policy ids: mock_id1, mock_id3')

    @patch.object(clc_common, '_get_policies')
    def test_find_policy_not_found(self, mock_get_policies):
        return_policies = [
            {'id': 'mock_id1', 'name': 'mock_name1'},
            {'id': 'mock_id2', 'name': 'mock_name2'}
        ]
        mock_get_policies.return_value = return_policies
        clc_auth = {'clc_alias': 'mock_alias'}

        policy = clc_common.find_policy(self.module, clc_auth, 'mock_name3',
                                        policy_type='alert')

        self.assertIsNone(policy)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_loadbalancer_list(self, mock_call_api):
        loadbalancer_existing = {'id': 'mock_id', 'name': 'mock_name'}
        mock_call_api.return_value = [loadbalancer_existing]

        clc_auth = {'clc_alias': 'mock_alias', 'clc_location': 'mock_dc'}
        result = clc_common.loadbalancer_list(self.module, clc_auth)

        self.assertEqual(result, [loadbalancer_existing])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_loadbalancer_list_exception(self, mock_call_api):
        error = ClcApiException('Failed')
        mock_call_api.side_effect = error

        clc_auth = {'clc_alias': 'mock_alias', 'clc_location': 'mock_dc'}
        result = clc_common.loadbalancer_list(self.module, clc_auth)

        self.module.fail_json.assert_called_once_with(
            msg='Unable to fetch load balancers for account: mock_alias '
                'in location: mock_dc. Failed')

    @patch.object(clc_common, 'loadbalancer_list')
    def test_find_loadbalancer(self, mock_loadbalancer_list):
        loadbalancer_existing = {'id': 'mock_id', 'name': 'mock_name'}
        mock_loadbalancer_list.return_value = [loadbalancer_existing]

        result = clc_common.find_loadbalancer(self.module, {},
                                              loadbalancer_existing['id'])

        self.assertEqual(result, loadbalancer_existing)

    @patch.object(clc_common, 'loadbalancer_list')
    def test_find_loadbalancer_exception(self, mock_loadbalancer_list):
        loadbalancer_existing = {'id': 'mock_id', 'name': 'mock_name'}
        mock_loadbalancer_list.return_value = [loadbalancer_existing,
                                               loadbalancer_existing]

        result = clc_common.find_loadbalancer(
            self.module, {}, loadbalancer_existing['name'])

        self.module.fail_json.assert_called_once_with(
            msg='Multiple load balancers matching: {search}. '
                'Load balancer ids: {ids}'.format(
                    search=loadbalancer_existing['name'],
                    ids=', '.join([loadbalancer_existing['id'],
                                   loadbalancer_existing['id']])))