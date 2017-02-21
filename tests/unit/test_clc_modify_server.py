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

import unittest
import mock
from mock import patch

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException

import clc_ansible_module.clc_modify_server as clc_modify_server
from clc_ansible_module.clc_modify_server import ClcModifyServer


class TestClcModifyServerFunctions(unittest.TestCase):

    def setUp(self):
        self.clc_auth = {'clc_alias': 'mock_alias', 'clc_location': 'mock_dc'}
        self.module = mock.MagicMock()
        self.module.check_mode = False
        self.module.params = {}
        self.datacenter = mock.MagicMock()

    @patch.object(ClcModifyServer, '_modify_servers')
    @patch.object(clc_common, 'authenticate')
    @patch.object(clc_common, 'call_clc_api')
    def test_process_request_state_absent_cpu_memory(
            self, mock_call_api, mock_authenticate, mock_modify):
        # Setup Test
        self.module.params = {
            'state': 'absent',
            'server_ids': ['TEST_SERVER'],
            'cpu': 2,
            'memory': 4,
            'wait': True
        }

        # Test
        under_test = ClcModifyServer(self.module)
        under_test.process_request()

        self.module.fail_json.assert_called_with(
            msg='\'absent\' state is not supported for '
                '\'cpu\' and \'memory\' arguments')

    @patch.object(ClcModifyServer, '_modify_servers')
    @patch.object(clc_common, 'authenticate')
    @patch.object(clc_common, 'call_clc_api')
    def test_process_request_state_present(
            self, mock_call_api, mock_authenticate, mock_modify):
        # Setup Test
        self.module.params = {
            'state': 'present',
            'server_ids': ['TEST_SERVER'],
            'wait': True
        }

        mock_modify.return_value = (True, [{'id': 'TEST_SERVER'}],
                                    ['TEST_SERVER'])

        # Test
        under_test = ClcModifyServer(self.module)
        under_test.process_request()

        mock_modify.assert_called_with(
            server_ids=['TEST_SERVER']
        )
        self.module.exit_json.assert_called_with(
            changed=True, server_ids=['TEST_SERVER'],
            servers=[{'id': 'TEST_SERVER'}])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_aa_policy_exists_on_server_true(self, mock_call_api):
        mock_call_api.return_value = {'id': 'policy_id'}
        under_test = ClcModifyServer(self.module)
        under_test.clc_auth = self.clc_auth
        result = under_test._aa_policy_exists_on_server('server_id',
                                                        'policy_id')
        self.assertTrue(result)

    @patch.object(clc_common, 'call_clc_api')
    def test_aa_policy_exists_on_server_false(self, mock_call_api):
        mock_call_api.return_value = {'id': 'policy_id'}
        under_test = ClcModifyServer(self.module)
        under_test.clc_auth = self.clc_auth
        result = under_test._aa_policy_exists_on_server('server_id',
                                                        'fake_id')
        self.assertFalse(result)

    @patch.object(clc_common, 'call_clc_api')
    def test_aa_policy_exists_on_server_exception(self, mock_call_api):
        mock_call_api.side_effect = ClcApiException('Failed', 400)
        under_test = ClcModifyServer(self.module)
        under_test.clc_auth = self.clc_auth
        result = under_test._aa_policy_exists_on_server('server_id',
                                                        'policy_id')
        self.module.fail_json.assert_called_once_with(
            msg='Unable to fetch anti affinity policy for server: server_id. '
                'Failed')

    @patch.object(clc_common, 'find_policy')
    @patch.object(clc_common, 'modify_aa_policy_on_server')
    @patch.object(ClcModifyServer, '_aa_policy_exists_on_server')
    def test_ensure_aa_policy_present(self, mock_pol_exists, mock_add_pol,
                                      mock_get_pol):
        mock_add_pol.return_value = 'OK'
        mock_pol_exists.return_value = False
        mock_get_pol.return_value = {'name': 'test', 'id': '123'}
        under_test = ClcModifyServer(self.module)
        under_test.module.params = {'anti_affinity_policy_name': 'test'}
        server = mock.MagicMock()
        server.id = 'server1'
        changed = under_test._ensure_aa_policy_present(server)
        self.assertEqual(changed, True)

    @patch.object(clc_common, 'find_policy')
    @patch.object(clc_common, 'modify_aa_policy_on_server')
    @patch.object(ClcModifyServer, '_aa_policy_exists_on_server')
    def test_ensure_aa_policy_present_not_found(self, mock_pol_exists,
                                                mock_add_pol,
                                                mock_get_pol):
        mock_get_pol.return_value = None
        under_test = ClcModifyServer(self.module)
        under_test.module.params = {'anti_affinity_policy_name': 'test'}
        server = mock.MagicMock()
        server.id = 'server1'
        changed = under_test._ensure_aa_policy_present(server)
        self.module.fail_json.assert_called_with(
            msg='No anti affinity policy matching: test.')

    @patch.object(clc_common, 'find_policy')
    @patch.object(clc_common, 'modify_aa_policy_on_server')
    @patch.object(ClcModifyServer, '_aa_policy_exists_on_server')
    def test_ensure_aa_policy_present_no_change(self, mock_pol_exists,
                                                mock_add_pol,
                                                mock_get_pol):
        mock_add_pol.return_value = 'OK'
        mock_pol_exists.return_value = False
        mock_get_pol.return_value = {'name': 'test', 'id': '123'}
        under_test = ClcModifyServer(self.module)
        under_test.module.params = {'anti_affinity_policy_name': 'test'}
        server = mock.MagicMock()
        server.id = 'server1'
        changed = under_test._ensure_aa_policy_present(server)
        self.assertEqual(changed, True)

    @patch.object(clc_common, 'find_policy')
    @patch.object(clc_common, 'remove_aa_policy_from_server')
    @patch.object(ClcModifyServer, '_aa_policy_exists_on_server')
    def test_ensure_aa_policy_absent(self, mock_pol_exists, mock_remove_pol,
                                     mock_get_pol):
        mock_remove_pol.return_value = 'OK'
        mock_pol_exists.return_value = True
        mock_get_pol.return_value = {'name': 'test', 'id': '123'}
        under_test = ClcModifyServer(self.module)
        under_test.module.params = {'anti_affinity_policy_name': 'test'}
        server = mock.MagicMock()
        server.id = 'server1'
        changed = under_test._ensure_aa_policy_absent(server)
        self.assertTrue(changed)

    @patch.object(clc_common, 'find_policy')
    @patch.object(clc_common, 'remove_aa_policy_from_server')
    @patch.object(ClcModifyServer, '_aa_policy_exists_on_server')
    def test_ensure_aa_policy_absent_not_found(self, mock_pol_exists,
                                               mock_remove_pol,
                                               mock_get_pol):
        mock_get_pol.return_value = None
        under_test = ClcModifyServer(self.module)
        under_test.module.params = {'anti_affinity_policy_name': 'test'}
        server = mock.MagicMock()
        server.id = 'server1'
        changed = under_test._ensure_aa_policy_absent(server)
        self.module.fail_json.assert_called_with(
            msg='No anti affinity policy matching: test.')

    @patch.object(clc_common, 'find_policy')
    @patch.object(clc_common, 'remove_aa_policy_from_server')
    @patch.object(ClcModifyServer, '_aa_policy_exists_on_server')
    def test_ensure_aa_policy_absent_no_change(self, mock_pol_exists,
                                               mock_remove_pol,
                                               mock_get_pol):
        under_test = ClcModifyServer(self.module)
        under_test.module.params = {}
        server = mock.MagicMock()
        server.id = 'server1'
        changed = under_test._ensure_aa_policy_absent(server)
        self.assertFalse(changed)

    def test_alert_policy_exists_on_server_true(self):
        server = mock.MagicMock()
        server.data = {
            'details': {
                'alertPolicies': [{'id': 123, 'name': 'test'}]
            }
        }
        under_test = ClcModifyServer(self.module)
        res = under_test._alert_policy_exists_on_server(server, 123)
        self.assertTrue(res)

    def test_alert_policy_exists_on_server_false(self):
        server = mock.MagicMock()
        server.data = {
            'details': {
                'alertPolicies': [{'id': 123, 'name': 'test'}]
            }
        }
        under_test = ClcModifyServer(self.module)
        res = under_test._alert_policy_exists_on_server(server, 111)
        self.assertFalse(res)

    @patch.object(clc_common, 'find_policy')
    @patch.object(clc_common, 'add_alert_policy_to_server')
    @patch.object(ClcModifyServer, '_alert_policy_exists_on_server')
    def test_ensure_alert_policy_present(self, mock_pol_exists, mock_add_pol,
                                         mock_get_pol):
        mock_add_pol.return_value = 'OK'
        mock_pol_exists.return_value = False
        mock_get_pol.return_value = {'name': 'test', 'id': '123'}
        under_test = ClcModifyServer(self.module)
        under_test.module.params = {'alert_policy_name': 'test'}
        server = mock.MagicMock()
        server.id = 'server1'
        changed = under_test._ensure_alert_policy_present(server)
        self.assertEqual(changed, True)

    @patch.object(clc_common, 'find_policy')
    @patch.object(clc_common, 'add_alert_policy_to_server')
    @patch.object(ClcModifyServer, '_alert_policy_exists_on_server')
    def test_ensure_alert_policy_present_not_found(self, mock_pol_exists,
                                                   mock_add_pol,
                                                   mock_get_pol):
        mock_get_pol.return_value = None
        under_test = ClcModifyServer(self.module)
        under_test.module.params = {'alert_policy_name': 'test'}
        server = mock.MagicMock()
        server.id = 'server1'
        changed = under_test._ensure_alert_policy_present(server)
        self.module.fail_json.assert_called_with(
            msg='No alert policy matching: test.')

    @patch.object(clc_common, 'find_policy')
    @patch.object(clc_common, 'add_alert_policy_to_server')
    @patch.object(ClcModifyServer, '_alert_policy_exists_on_server')
    def test_ensure_alert_policy_present_no_change(self, mock_pol_exists,
                                                   mock_add_pol,
                                                   mock_get_pol):
        mock_add_pol.return_value = 'OK'
        mock_pol_exists.return_value = False
        mock_get_pol.return_value = {'name': 'test', 'id': '123'}
        under_test = ClcModifyServer(self.module)
        under_test.module.params = {'alert_policy_name': 'test'}
        server = mock.MagicMock()
        server.id = 'server1'
        changed = under_test._ensure_alert_policy_present(server)
        self.assertEqual(changed, True)

    @patch.object(clc_common, 'find_policy')
    @patch.object(clc_common, 'remove_alert_policy_from_server')
    @patch.object(ClcModifyServer, '_alert_policy_exists_on_server')
    def test_ensure_alert_policy_absent(self, mock_pol_exists, mock_remove_pol,
                                        mock_get_pol):
        mock_remove_pol.return_value = 'OK'
        mock_pol_exists.return_value = True
        mock_get_pol.return_value = {'name': 'test', 'id': '123'}
        under_test = ClcModifyServer(self.module)
        under_test.module.params = {'alert_policy_name': 'test'}
        server = mock.MagicMock()
        server.id = 'server1'
        changed = under_test._ensure_alert_policy_absent(server)
        self.assertTrue(changed)

    @patch.object(clc_common, 'find_policy')
    @patch.object(clc_common, 'remove_alert_policy_from_server')
    @patch.object(ClcModifyServer, '_alert_policy_exists_on_server')
    def test_ensure_alert_policy_absent_not_found(self, mock_pol_exists,
                                                  mock_remove_pol,
                                                  mock_get_pol):
        mock_get_pol.return_value = None
        under_test = ClcModifyServer(self.module)
        under_test.module.params = {'alert_policy_name': 'test'}
        server = mock.MagicMock()
        server.id = 'server1'
        changed = under_test._ensure_alert_policy_absent(server)
        self.module.fail_json.assert_called_with(
            msg='No alert policy matching: test.')

    @patch.object(clc_common, 'find_policy')
    @patch.object(clc_common, 'remove_alert_policy_from_server')
    @patch.object(ClcModifyServer, '_alert_policy_exists_on_server')
    def test_ensure_alert_policy_absent_no_change(self, mock_pol_exists,
                                                  mock_remove_pol,
                                                  mock_get_pol):
        under_test = ClcModifyServer(self.module)
        under_test.module.params = {}
        server = mock.MagicMock()
        server.id = 'server1'
        changed = under_test._ensure_alert_policy_absent(server)
        self.assertFalse(changed)

    @patch.object(clc_common, 'servers_by_id')
    @patch.object(ClcModifyServer, '_ensure_server_config')
    @patch.object(clc_common, 'call_clc_api')
    def test_modify_servers_present(self, mock_call_api, mock_ensure_config,
                                    mock_get_servers):
        module = self.module
        module.params = {
            'state': 'present',
            'wait': True
        }
        mock_ensure_config.return_value = mock.MagicMock(), mock.MagicMock()
        server1 = mock.MagicMock()
        server_ids = ['server1']
        server1.id = 'server1'
        mock_get_servers.return_value = [server1]
        under_test = ClcModifyServer(module)
        changed, server, result = under_test._modify_servers(server_ids)
        self.assertEqual(changed, True)
        self.assertEqual(result[0], 'server1')

    @patch.object(clc_common, 'servers_by_id')
    @patch.object(ClcModifyServer, '_ensure_alert_policy_absent')
    @patch.object(ClcModifyServer, '_ensure_aa_policy_absent')
    @patch.object(clc_common, 'call_clc_api')
    def test_modify_servers_absent(self, mock_call_api, mock_ensure_aa_pol,
                                   mock_ensure_alert_pol, mock_get_servers):
        module = self.module
        module.params = {
            'state': 'absent',
            'wait': True
        }
        mock_ensure_aa_pol.return_value = True
        mock_ensure_alert_pol.return_value = True
        server1 = mock.MagicMock()
        server_ids = ['server1']
        server1.id = 'server1'
        mock_get_servers.return_value = [server1]
        under_test = ClcModifyServer(module)
        changed, server, result = under_test._modify_servers(server_ids)
        self.assertEqual(changed, True)
        self.assertEqual(result[0], 'server1')

    def test_modify_servers_empty_servers(self):
        under_test = ClcModifyServer(self.module)
        under_test._modify_servers([])
        self.module.fail_json.assert_called_once_with(msg='server_ids should be a list of servers, aborting')

    @patch.object(ClcModifyServer, '_modify_clc_server')
    def test_ensure_server_config_change_cpu(self, mock_modify_server):
        mock_modify_server.return_value = 'OK'
        mock_server = mock.MagicMock()
        mock_server.data = {'details': {'cpu': 1, 'memoryGB': 1}}
        self.module.check_mode = False
        under_test = ClcModifyServer(self.module)
        under_test.module.params = {'cpu': 2}
        changed, res = under_test._ensure_server_config(mock_server)
        self.assertEqual(changed, True)
        self.assertEqual(res, 'OK')

    @patch.object(ClcModifyServer, '_modify_clc_server')
    def test_ensure_server_config_change_memory(self, mock_modify_server):
        mock_modify_server.return_value = 'OK'
        mock_server = mock.MagicMock()
        mock_server.data = {'details': {'cpu': 1, 'memoryGB': 1}}
        self.module.check_mode = False
        under_test = ClcModifyServer(self.module)
        under_test.module.params = {'memory': 2}
        changed, res = under_test._ensure_server_config(mock_server)
        self.assertEqual(changed, True)
        self.assertEqual(res, 'OK')

    @patch.object(ClcModifyServer, '_modify_clc_server')
    def test_ensure_server_config_change_cpu_and_memory(self, mock_modify_server):
        mock_modify_server.return_value = 'OK'
        mock_server = mock.MagicMock()
        mock_server.data = {'details': {'cpu': 1, 'memoryGB': 1}}
        self.module.check_mode = False
        under_test = ClcModifyServer(self.module)
        under_test.module.params = {'cpu': 2, 'memory': 2}
        changed, res = under_test._ensure_server_config(mock_server)
        self.assertEqual(changed, True)
        self.assertEqual(res, 'OK')

    @patch.object(ClcModifyServer, '_modify_clc_server')
    def test_ensure_server_config_no_change(self, mock_modify_server):
        mock_modify_server.return_value = 'OK'
        mock_server = mock.MagicMock()
        mock_server.data = {'details': {'cpu': 1, 'memoryGB': 1}}
        self.module.check_mode = False
        under_test = ClcModifyServer(self.module)
        under_test.module.params = {'cpu': 1, 'memory': 1}
        changed, res = under_test._ensure_server_config(mock_server)
        self.assertEqual(changed, False)
        self.assertEqual(res, None)

    @patch.object(clc_common, 'call_clc_api')
    def test_modify_clc_server(self, mock_call_api):
        mock_response = mock.MagicMock()
        mock_call_api.return_value = mock_response
        under_test = ClcModifyServer(self.module)
        under_test.clc_auth = self.clc_auth
        result = under_test._modify_clc_server('dummy_server', 1, 2)
        self.assertEqual(result, mock_response)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_modify_clc_server_exception(self, mock_call_api):
        error = ClcApiException('Mock failure message')
        mock_call_api.side_effect = error
        under_test = ClcModifyServer(self.module)
        under_test.clc_auth = self.clc_auth
        under_test._modify_clc_server('dummy_server', 1, 2)
        self.module.fail_json.assert_called_once_with(
            msg='Unable to update the server configuration for '
                'server: dummy_server. Mock failure message')

    @patch.object(clc_common, 'wait_on_completed_operations')
    @patch.object(clc_common, 'operation_id_list')
    def test_wait_for_requests_fail(self, mock_id_list, mock_wait_on_ops):
        self.module.params = {'wait': True}
        mock_wait_on_ops.return_value = 1
        under_test = ClcModifyServer(self.module)
        mock_request = mock.MagicMock()
        under_test._wait_for_requests([mock_request])
        self.module.fail_json.assert_called_with(msg='Unable to process modify server request')

    @patch.object(clc_common, 'servers_by_id')
    def test_refresh_servers_fail(self, mock_get_servers):
        error = ClcApiException('Mock fail message')
        mock_get_servers.side_effect = error
        under_test = ClcModifyServer(self.module)
        mock_server = mock.MagicMock()
        mock_server.id = 'mock_server_id'
        mock_servers = [mock_server]
        under_test._refresh_servers(self.module, mock_servers)
        self.module.fail_json.assert_called_with(
            msg='Unable to refresh servers. Mock fail message')

    @patch.object(clc_common, 'find_network')
    def test_find_network_id(self, mock_find_network):
        # Setup
        mock_network = mock.MagicMock()
        mock_network.name = 'TestReturnVlan'
        mock_network.id = '12345678123456781234567812345678'
        datacenter = 'mock_dc'

        mock_find_network.return_value = mock_network
        self.module.params = {'additional_network': mock_network.id}

        # Function Under Test
        under_test = ClcModifyServer(self.module)
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        result = under_test._find_network_id(datacenter)

        # Assert Result
        self.assertEqual(result, mock_network.id)
        self.assertEqual(self.module.fail_json.called, False)

    @patch.object(clc_common, 'find_network')
    def test_find_network_id_not_found(self, mock_find_network):
        # Setup
        mock_network = mock.MagicMock()
        mock_network.name = 'TestReturnVlan'
        mock_network.id = '12345678123456781234567812345678'
        datacenter = 'mock_dc'

        mock_find_network.return_value = None
        self.module.params = {'additional_network': mock_network.name}

        # Function Under Test
        under_test = ClcModifyServer(self.module)
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        result = under_test._find_network_id(datacenter)

        # Assert Result
        self.module.fail_json.assert_called_with(
            msg='No matching network: TestReturnVlan found in '
                'location: mock_dc')

    def test_find_datacenter(self):
        params = {
            'state': 'present',
        }
        under_test = ClcModifyServer(self.module)
        under_test.module.params = params
        under_test.clc_auth = self.clc_auth

        ret = under_test._find_datacenter()

        self.assertEqual(ret, self.clc_auth['clc_location'])

    @patch.object(clc_common, 'authenticate')
    def test_find_datacenter_error(self, mock_authenticate):
        error = ClcApiException()
        mock_authenticate.side_effect = error
        params = {
            'state': 'present',
            'location': 'testdc'
        }
        under_test = ClcModifyServer(self.module)
        under_test.module.params = params
        under_test._find_datacenter()
        self.module.fail_json.assert_called_with(
            msg='Unable to find location: testdc')

    @patch.object(ClcModifyServer, '_modify_add_nic')
    def test_ensure_nic_present_change(self, add_nic):
        add_nic.return_value = True
        mock_server = mock.MagicMock()
        mock_server_params = {
            'additional_network': 'test'
        }
        under_test = ClcModifyServer(self.module)
        under_test.module.params = mock_server_params
        changed = under_test._ensure_nic_present(mock_server)
        self.assertEqual(changed, True)

    @patch.object(ClcModifyServer, '_modify_add_nic')
    def test_ensure_nic_present_no_change(self, add_nic):
        add_nic.return_value = False
        mock_server = mock.MagicMock()
        mock_server_params = {
            'additional_network': 'test'
        }
        under_test = ClcModifyServer(self.module)
        under_test.module.params = mock_server_params
        changed = under_test._ensure_nic_present(mock_server)
        self.assertEqual(changed, False)

    @patch.object(clc_common, 'servers_by_id')
    @patch.object(ClcModifyServer, '_ensure_alert_policy_absent')
    @patch.object(ClcModifyServer, '_ensure_aa_policy_absent')
    @patch.object(ClcModifyServer, '_ensure_nic_absent')
    @patch.object(clc_common, 'call_clc_api')
    def test_modify_servers_calls_ensure_nic_absent(
            self, mock_call_api, mock_ensure_nic_absent, mock_ensure_aa_pol,
            mock_ensure_alert_pol, mock_get_servers):
        module = self.module
        module.params = {
            'state': 'absent',
            'wait': True
        }
        mock_ensure_aa_pol.return_value = False
        mock_ensure_alert_pol.return_value = False
        mock_ensure_nic_absent.return_value = True
        server1 = mock.MagicMock()
        server_ids = ['server1']
        server1.id = 'server1'
        mock_get_servers.return_value = [server1]
        under_test = ClcModifyServer(module)
        changed, server, result = under_test._modify_servers(server_ids)
        self.assertEqual(changed, True)

    @patch.object(ClcModifyServer, '_modify_remove_nic')
    def test_ensure_nic_absent_change(self, mock_remove_nic):
        mock_server = mock.MagicMock
        mock_server.id = 'test_id'
        mock_remove_nic.return_value = True

        under_test = ClcModifyServer(self.module)
        under_test.module.params = {'additional_network': 'mock_net'}
        result = under_test._ensure_nic_absent(mock_server)

        self.assertTrue(result)

    @patch.object(ClcModifyServer, '_modify_remove_nic')
    def test_ensure_nic_absent_no_change(self, mock_remove_nic):
        mock_server = mock.MagicMock()

        under_test = ClcModifyServer(self.module)
        under_test.module.params = {}
        result = under_test._ensure_nic_absent(mock_server)

        self.assertFalse(result)

    @patch.object(ClcModifyServer, '_find_datacenter')
    @patch.object(ClcModifyServer, '_find_network_id')
    def test_modify_add_nic_returns_none_if_check_mode(
            self, mock_find_network, mock_find_dc):
        mock_find_dc.return_value = self.clc_auth['clc_location']
        mock_find_network.return_value = 'mock_network'

        self.module.check_mode = True
        under_test = ClcModifyServer(self.module)
        under_test.clc_auth = self.clc_auth

        result = under_test._modify_add_nic('mock_id')

        self.assertIsNone(result)

    @patch.object(ClcModifyServer, '_find_datacenter')
    @patch.object(ClcModifyServer, '_find_network_id')
    @patch.object(ClcModifyServer, '_wait_for_requests')
    @patch.object(clc_common, 'call_clc_api')
    def test_modify_add_nic(
            self, mock_call_api, mock_wait, mock_find_network, mock_find_dc):
        mock_find_dc.return_value = self.clc_auth['clc_location']
        mock_find_network.return_value = 'mock_network'
        mock_response = mock.MagicMock()
        mock_call_api.return_value = mock_response

        under_test = ClcModifyServer(self.module)
        under_test.clc_auth = self.clc_auth

        result = under_test._modify_add_nic('mock_id')

        self.assertTrue(result)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcModifyServer, '_find_datacenter')
    @patch.object(ClcModifyServer, '_find_network_id')
    @patch.object(ClcModifyServer, '_wait_for_requests')
    @patch.object(clc_common, 'call_clc_api')
    def test_modify_add_nic_exception(
            self, mock_call_api, mock_wait, mock_find_network, mock_find_dc):
        mock_find_dc.return_value = self.clc_auth['clc_location']
        mock_find_network.return_value = 'mock_network'
        mock_call_api.side_effect = ClcApiException('Mock failure message')

        under_test = ClcModifyServer(self.module)
        under_test.clc_auth = self.clc_auth

        result = under_test._modify_add_nic('mock_id')

        self.module.fail_json.assert_called_with(
            msg='Unable to add NIC to server: mock_id. '
                'Mock failure message')

    @patch.object(ClcModifyServer, '_find_datacenter')
    @patch.object(ClcModifyServer, '_find_network_id')
    @patch.object(ClcModifyServer, '_wait_for_requests')
    @patch.object(clc_common, 'call_clc_api')
    def test_modify_add_nic_exception_graceful(
            self, mock_call_api, mock_wait, mock_find_network, mock_find_dc):
        mock_find_dc.return_value = self.clc_auth['clc_location']
        mock_find_network.return_value = 'mock_network'
        mock_call_api.side_effect = ClcApiException(
            'Server \'mock_id\' already has an adapter for network '
            '\'mock_network\'')

        under_test = ClcModifyServer(self.module)
        under_test.clc_auth = self.clc_auth

        result = under_test._modify_add_nic('mock_id')

        self.assertFalse(result)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcModifyServer, '_find_datacenter')
    @patch.object(ClcModifyServer, '_find_network_id')
    def test_modify_remove_nic_returns_none_if_check_mode(
            self, mock_find_network, mock_find_dc):
        mock_find_dc.return_value = self.clc_auth['clc_location']
        mock_find_network.return_value = 'mock_network'

        self.module.check_mode = True
        under_test = ClcModifyServer(self.module)
        under_test.clc_auth = self.clc_auth

        result = under_test._modify_remove_nic('mock_id')

        self.assertIsNone(result)

    @patch.object(ClcModifyServer, '_find_datacenter')
    @patch.object(ClcModifyServer, '_find_network_id')
    @patch.object(ClcModifyServer, '_wait_for_requests')
    @patch.object(clc_common, 'call_clc_api')
    def test_modify_remove_nic(
            self, mock_call_api, mock_wait, mock_find_network, mock_find_dc):
        mock_find_dc.return_value = self.clc_auth['clc_location']
        mock_find_network.return_value = 'mock_network'
        mock_response = mock.MagicMock()
        mock_call_api.return_value = mock_response

        under_test = ClcModifyServer(self.module)
        under_test.clc_auth = self.clc_auth

        result = under_test._modify_remove_nic('mock_id')

        self.assertTrue(result)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcModifyServer, '_find_datacenter')
    @patch.object(ClcModifyServer, '_find_network_id')
    @patch.object(ClcModifyServer, '_wait_for_requests')
    @patch.object(clc_common, 'call_clc_api')
    def test_modify_remove_nic_exception(
            self, mock_call_api, mock_wait, mock_find_network, mock_find_dc):
        mock_find_dc.return_value = self.clc_auth['clc_location']
        mock_find_network.return_value = 'mock_network'
        mock_call_api.side_effect = ClcApiException('Mock failure message')

        under_test = ClcModifyServer(self.module)
        under_test.clc_auth = self.clc_auth

        result = under_test._modify_remove_nic('mock_id')

        self.module.fail_json.assert_called_with(
            msg='Unable to remove NIC from server: mock_id. '
                'Mock failure message')

    @patch.object(ClcModifyServer, '_find_datacenter')
    @patch.object(ClcModifyServer, '_find_network_id')
    @patch.object(ClcModifyServer, '_wait_for_requests')
    @patch.object(clc_common, 'call_clc_api')
    def test_modify_remove_nic_exception_graceful(
            self, mock_call_api, mock_wait, mock_find_network, mock_find_dc):
        mock_find_dc.return_value = self.clc_auth['clc_location']
        mock_find_network.return_value = 'mock_network'
        mock_call_api.side_effect = ClcApiException(
            'Server \'mock_id\' has no secondary adapter for network '
            '\'mock_network\'')

        under_test = ClcModifyServer(self.module)
        under_test.clc_auth = self.clc_auth

        result = under_test._modify_remove_nic('mock_id')

        self.assertFalse(result)
        self.assertFalse(self.module.fail_json.called)


if __name__ == '__main__':
    unittest.main()
