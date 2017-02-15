#!/usr/bin/python
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

import mock
from mock import patch
import unittest

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException

import clc_ansible_module.clc_publicip as clc_publicip
from clc_ansible_module.clc_publicip import ClcPublicIp


class TestClcPublicIpFunctions(unittest.TestCase):


    def setUp(self):
        self.module = mock.MagicMock()
        self.clc_auth = {'clc_alias': 'mock_alias', 'clc_location': 'mock_dc'}

        mock_server1 = mock.MagicMock()
        mock_server1.id = 'mock_id1'
        mock_server1.data = {
            'ipaddress': '1.2.3.4',
            'publicip': '2.4.6.8',
            'details': {
                'ipAddresses': [
                    {'internal': '1.2.3.4',
                     'public': '2.4.6.8'},
                    {'internal': '1.1.1.1',
                     'public': '2.2.2.2'}
                ]
            }
        }
        self.mock_server1 = mock_server1
        mock_server2 = mock.MagicMock()
        mock_server2.id = 'mock_id2',
        mock_server2.data = {
            'ipaddress': '5.6.7.8',
            'details': {
                'ipAddresses': [{
                    'internal': '5.6.7.8'
                }]
            }
        }
        self.mock_server2 = mock_server2

    def test_define_argument_spec(self):
        result = ClcPublicIp._define_module_argument_spec()
        self.assertIsInstance(result, dict)
        self.assertTrue('argument_spec' in result)
        self.assertTrue('mutually_exclusive' in result)
        result = ClcPublicIp._define_module_argument_spec()

    @patch.object(clc_common, 'wait_on_completed_operations')
    @patch.object(clc_common, 'operation_id_list')
    def test_wait_for_requests_to_complete_req_successful(
            self, mock_operation_id, mock_wait):
        mock_request_list = [mock.MagicMock()]
        mock_wait.return_value = 0

        under_test = ClcPublicIp(self.module)
        under_test.module.params = {'wait': True}

        under_test._wait_for_requests_to_complete(mock_request_list)

        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'wait_on_completed_operations')
    @patch.object(clc_common, 'operation_id_list')
    def test_wait_for_requests_to_complete_req_failed(
        self, mock_operation_id, mock_wait):
        mock_request_list = [mock.MagicMock()]
        mock_wait.return_value = 1

        under_test = ClcPublicIp(self.module)
        under_test.module.params = {'wait': True}

        under_test._wait_for_requests_to_complete(mock_request_list)

        self.module.fail_json.assert_called_once_with(
            msg='Unable to process public ip request')

    def test_wait_for_requests_no_wait(self):
        mock_request = mock.MagicMock()
        self.module.params = {
            'wait': False
        }
        under_test = ClcPublicIp(self.module)
        under_test._wait_for_requests_to_complete([mock_request])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcPublicIp, '_delete_publicip')
    def test_remove_publicip_addresses_no_internal(self, mock_delete):
        mock_response = mock.MagicMock()
        mock_delete.return_value = mock_response
        server = self.mock_server1

        under_test = ClcPublicIp(self.module)
        under_test.module.params = {}
        results = under_test._remove_publicip_addresses(server)

        self.assertEqual(len(results), 2)

    @patch.object(ClcPublicIp, '_delete_publicip')
    def test_remove_publicip_addresses_with_internal(self, mock_delete):
        mock_response = mock.MagicMock()
        mock_delete.return_value = mock_response
        server = self.mock_server1

        under_test = ClcPublicIp(self.module)
        under_test.module.params = {'internal_ip': server.data['ipaddress']}
        results = under_test._remove_publicip_addresses(server)

        self.assertEqual(len(results), 1)

    @patch.object(ClcPublicIp, '_delete_publicip')
    def test_remove_publicip_addresses_no_public(self, mock_delete):
        mock_response = mock.MagicMock()
        mock_delete.return_value = mock_response
        server = self.mock_server2

        under_test = ClcPublicIp(self.module)
        under_test.module.params = {}
        results = under_test._remove_publicip_addresses(server)

        self.assertEqual(len(results), 0)

    @patch.object(clc_common, 'authenticate')
    @patch.object(ClcPublicIp, 'ensure_public_ip_present')
    def test_process_request_state_present(self, mock_ensure_present,
                                           mock_authenticate):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2'],
            'protocol': 'TCP',
            'ports': [80, 90],
            'wait': True,
            'state': 'present'
        }
        mock_ensure_present.return_value = (True, ['TESTSVR1'],
                                            mock.MagicMock())
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcPublicIp(self.module)
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(
            changed=True, server_ids=['TESTSVR1'])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'authenticate')
    @patch.object(ClcPublicIp, 'ensure_public_ip_absent')
    def test_process_request_state_absent(self, mock_ensure_absent,
                                          mock_authenticate):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2'],
            'protocol': 'TCP',
            'ports': [80, 90],
            'wait': True,
            'state': 'absent'
        }
        mock_ensure_absent.return_value = (True, ['TESTSVR1','TESTSVR2'],
                                            mock.MagicMock())
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcPublicIp(self.module)
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(
            changed=True, server_ids=['TESTSVR1', 'TESTSVR2'])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'servers_by_id')
    @patch.object(ClcPublicIp, '_update_publicip_required')
    @patch.object(ClcPublicIp, '_update_publicip')
    @patch.object(ClcPublicIp, '_add_publicip')
    def test_ensure_public_ip_present_add(
            self, mock_add, mock_update, mock_update_needed, mock_servers):
        params = {
            'server_ids': [self.mock_server2.id],
            'protocol': 'TCP',
            'ports': [80]
        }
        mock_servers.return_value = [self.mock_server2]
        mock_response = mock.MagicMock()
        mock_add.return_value = mock_response

        self.module.check_mode = False
        under_test = ClcPublicIp(self.module)
        under_test.module.params = params

        changed, servers, results = under_test.ensure_public_ip_present()

        self.assertTrue(changed)
        self.assertEqual(servers, [self.mock_server2.id])
        self.assertEqual(len(results), 1)

        self.assertTrue(mock_add.called)
        self.assertFalse(mock_update.called)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'servers_by_id')
    @patch.object(ClcPublicIp, '_update_publicip_required')
    @patch.object(ClcPublicIp, '_update_publicip')
    @patch.object(ClcPublicIp, '_add_publicip')
    def test_ensure_public_ip_present_update(
            self, mock_add, mock_update, mock_update_needed, mock_servers):
        params = {
            'server_id': self.mock_server1.id,
            'internal_ip': self.mock_server1.data['ipaddress'],
            'protocol': 'TCP',
            'ports': [80, 443],
            'source_restrictions': ['1.2.3.0/24']
        }
        mock_servers.return_value = [self.mock_server1]
        mock_update_needed.return_value = True
        mock_response = mock.MagicMock()
        mock_update.return_value = mock_response

        self.module.check_mode = False
        under_test = ClcPublicIp(self.module)
        under_test.module.params = params

        changed, servers, results = under_test.ensure_public_ip_present()

        self.assertTrue(changed)
        self.assertEqual(servers, [self.mock_server1.id])
        self.assertEqual(len(results), 1)

        self.assertFalse(mock_add.called)
        self.assertTrue(mock_update.called)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'servers_by_id')
    @patch.object(ClcPublicIp, '_update_publicip_required')
    @patch.object(ClcPublicIp, '_update_publicip')
    @patch.object(ClcPublicIp, '_add_publicip')
    def test_ensure_public_ip_present_update_not_needed(
            self, mock_add, mock_update, mock_update_needed, mock_servers):
        params = {
            'server_id': self.mock_server1.id,
            'internal_ip': self.mock_server1.data['ipaddress'],
            'protocol': 'TCP',
            'ports': [80, 443]
        }
        mock_servers.return_value = [self.mock_server1]
        mock_update_needed.return_value = False
        mock_response = mock.MagicMock()
        mock_update.return_value = mock_response

        self.module.check_mode = False
        under_test = ClcPublicIp(self.module)
        under_test.module.params = params

        changed, servers, results = under_test.ensure_public_ip_present()

        self.assertFalse(changed)
        self.assertEqual(servers, [])
        self.assertEqual(len(results), 0)

        self.assertFalse(mock_add.called)
        self.assertFalse(mock_update.called)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'servers_by_id')
    @patch.object(ClcPublicIp, '_update_publicip_required')
    @patch.object(ClcPublicIp, '_update_publicip')
    @patch.object(ClcPublicIp, '_add_publicip')
    def test_ensure_public_ip_present_update_bad_ip(
            self, mock_add, mock_update, mock_update_needed, mock_servers):
        params = {
            'server_id': self.mock_server1.id,
            'internal_ip': '0.0.0.0',
            'protocol': 'TCP',
            'ports': [80, 443]
        }
        mock_servers.return_value = [self.mock_server1]
        mock_update_needed.return_value = True
        mock_response = mock.MagicMock()
        mock_update.return_value = mock_response

        self.module.check_mode = False
        under_test = ClcPublicIp(self.module)
        under_test.module.params = params

        under_test.ensure_public_ip_present()

        self.module.fail_json.assert_called_once_with(
            msg='Internal IP address: 0.0.0.0 is not present on '
                'server: {id}.'.format(id=self.mock_server1.id))

    def test_ensure_public_ip_present_no_servers(self):
        under_test = ClcPublicIp(self.module)
        under_test.module.params = {
            'ports': [80],
            'protocol': 'TCP'
        }
        under_test.ensure_public_ip_present()
        self.module.fail_json.assert_called_once_with(
            msg='Must specify either server_id or server_ids.')

    def test_ensure_public_ip_present_no_servers(self):
        under_test = ClcPublicIp(self.module)
        under_test.module.params = {
            'server_id': 'mock_id',
            'protocol': 'TCP'
        }
        under_test.ensure_public_ip_present()
        self.module.fail_json.assert_called_once_with(
            msg='Must specify protocol and ports when state is present.')


    @patch.object(clc_common, 'servers_by_id')
    @patch.object(ClcPublicIp, '_delete_publicip')
    def test_ensure_publicip_absent_remove(self, mock_delete, mock_servers):
        mock_response = mock.MagicMock()
        mock_delete.return_value = mock_response
        mock_servers.return_value = [self.mock_server1, self.mock_server2]
        params = {
            'server_ids': [self.mock_server1.id, self.mock_server2.id]
        }

        under_test = ClcPublicIp(self.module)
        under_test.module.params = params
        under_test.module.check_mode = False

        changed, servers, results = under_test.ensure_public_ip_absent()

        self.assertFalse(self.module.fail_json.called)
        self.assertTrue(changed)
        self.assertEqual(servers, [self.mock_server1.id])
        self.assertEqual(len(results), 2)

    def test_ensure_publicip_absent_no_ids(self):
        under_test = ClcPublicIp(self.module)
        under_test.module.params = {}

        under_test.ensure_public_ip_absent()

        self.module.fail_json.assert_called_once_with(
            msg='Must specify either server_id or server_ids.')

    @patch.object(clc_common, 'servers_by_id')
    @patch.object(ClcPublicIp, '_remove_publicip_addresses')
    def test_ensure_publicip_absent_no_public_ip(self, mock_remove_ips,
                                                      mock_servers):
        mock_servers.return_value = [self.mock_server2]
        params = {
            'server_id': self.mock_server2.id
        }

        under_test = ClcPublicIp(self.module)
        under_test.module.params = params
        under_test.module.check_mode = False

        changed, servers, results = under_test.ensure_public_ip_absent()

        self.assertFalse(self.module.fail_json.called)
        self.assertFalse(changed)
        self.assertEqual(servers, [])

    @patch.object(clc_common, 'servers_by_id')
    @patch.object(ClcPublicIp, '_delete_publicip')
    def test_ensure_publicip_absent_internal_ip(self, mock_delete, mock_servers):
        mock_response = mock.MagicMock()
        mock_delete.return_value = mock_response
        mock_servers.return_value = [self.mock_server1]
        params = {
            'server_id': self.mock_server1.id,
            'internal_ip': self.mock_server1.data['ipaddress']
        }

        under_test = ClcPublicIp(self.module)
        under_test.module.params = params
        under_test.module.check_mode = False

        changed, servers, results = under_test.ensure_public_ip_absent()

        self.assertFalse(self.module.fail_json.called)
        self.assertTrue(changed)
        self.assertEqual(servers, [self.mock_server1.id])
        self.assertEqual(len(results), 1)

    @patch.object(clc_common, 'call_clc_api')
    def test_add_publicip(self, mock_call_api):
        mock_ports = mock.MagicMock()
        mock_restrictions = mock.MagicMock()
        mock_response = mock.MagicMock()
        mock_call_api.return_value = mock_response

        under_test = ClcPublicIp(self.module)
        under_test.clc_auth = self.clc_auth

        server = self.mock_server1
        result = under_test._add_publicip(server, mock_ports, mock_restrictions)

        self.assertEqual(result, mock_response)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_add_publicip_exception(self, mock_call_api):
        mock_ports = mock.MagicMock()
        mock_restrictions = mock.MagicMock()
        error = ClcApiException('Failed')
        mock_call_api.side_effect = error

        under_test = ClcPublicIp(self.module)
        under_test.clc_auth = self.clc_auth

        server = self.mock_server1
        result = under_test._add_publicip(server, mock_ports, mock_restrictions)

        self.module.fail_json.assert_called_once_with(
            msg='Failed to add public ip to the server: {id}. '
                'Failed'.format(id=server.id))

    @patch.object(clc_common, 'call_clc_api')
    def test_update_public_ip_required_none(self, mock_call_api):
        result = {
            'ports': [
                {'protocol': 'TCP', 'port': 443}
            ],
            'sourceRestrictions': [
                {'cidr': '1.2.3.0/24'}
            ]
        }
        mock_call_api.return_value = result

        under_test = ClcPublicIp(self.module)
        under_test.clc_auth = self.clc_auth

        update_needed = under_test._update_publicip_required(
            self.mock_server1, self.mock_server1.data['publicip'],
            result['ports'], result['sourceRestrictions'])

        self.assertFalse(update_needed)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_update_public_ip_required_port_change(self, mock_call_api):
        result = {
            'ports': [
                {'protocol': 'TCP', 'port': 443}
            ],
            'sourceRestrictions': [
                {'cidr': '1.2.3.0/24'}
            ]
        }
        new_ports = list(result['ports'])
        new_ports.append({'protocol': 'TCP', 'port': 80})
        mock_call_api.return_value = result

        under_test = ClcPublicIp(self.module)
        under_test.clc_auth = self.clc_auth

        update_needed = under_test._update_publicip_required(
            self.mock_server1, self.mock_server1.data['publicip'],
            new_ports, result['sourceRestrictions'])

        self.assertTrue(update_needed)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_update_public_ip_required_restriction_change(self, mock_call_api):
        result = {
            'ports': [
                {'protocol': 'TCP', 'port': 443}
            ],
            'sourceRestrictions': [
                {'cidr': '1.2.3.0/24'}
            ]
        }
        mock_call_api.return_value = result

        under_test = ClcPublicIp(self.module)
        under_test.clc_auth = self.clc_auth

        update_needed = under_test._update_publicip_required(
            self.mock_server1, self.mock_server1.data['publicip'],
            result['ports'], [])

        self.assertTrue(update_needed)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_update_public_ip_required_exception(self, mock_call_api):
        result = {
            'ports': [
                {'protocol': 'TCP', 'port': 443}
            ],
            'sourceRestrictions': [
                {'cidr': '1.2.3.0/24'}
            ]
        }
        mock_call_api.side_effect = ClcApiException('Failed')

        under_test = ClcPublicIp(self.module)
        under_test.clc_auth = self.clc_auth

        update_needed = under_test._update_publicip_required(
            self.mock_server1, self.mock_server1.data['publicip'],
            result['ports'], result['sourceRestrictions'])

        self.module.fail_json.assert_called_once_with(
            msg='Failed to get public ip: {ip} on the server: {id}. '
                'Failed'.format(id=self.mock_server1.id,
                                ip=self.mock_server1.data['publicip']))

    @patch.object(clc_common, 'call_clc_api')
    def test_update_publicip(self, mock_call_api):
        mock_ports = mock.MagicMock()
        mock_restrictions = mock.MagicMock()
        mock_response = mock.MagicMock()
        mock_call_api.return_value = mock_response

        under_test = ClcPublicIp(self.module)
        under_test.clc_auth = self.clc_auth

        server = self.mock_server1
        result = under_test._update_publicip(server, server.data['publicip'],
                                             mock_ports, mock_restrictions)

        self.assertEqual(result, mock_response)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_update_publicip_exception(self, mock_call_api):
        mock_ports = mock.MagicMock()
        mock_restrictions = mock.MagicMock()
        error = ClcApiException('Failed')
        mock_call_api.side_effect = error

        under_test = ClcPublicIp(self.module)
        under_test.clc_auth = self.clc_auth

        server = self.mock_server1
        result = under_test._update_publicip(server, server.data['publicip'],
                                             mock_ports, mock_restrictions)

        self.module.fail_json.assert_called_once_with(
            msg='Failed to update public ip: {ip} on the server: {id}. '
                'Failed'.format(id=server.id, ip=server.data['publicip']))

    @patch.object(clc_common, 'call_clc_api')
    def test_delete_publicip(self, mock_call_api):
        mock_response = mock.MagicMock()
        mock_call_api.return_value = mock_response

        under_test = ClcPublicIp(self.module)
        under_test.clc_auth = self.clc_auth

        server = self.mock_server1
        result = under_test._delete_publicip(server, server.data['publicip'])

        self.assertEqual(result, mock_response)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_delete_publicip_exception(self, mock_call_api):
        error = ClcApiException('Failed')
        mock_call_api.side_effect = error

        under_test = ClcPublicIp(self.module)
        under_test.clc_auth = self.clc_auth

        server = self.mock_server1
        result = under_test._delete_publicip(server, server.data['publicip'])

        self.module.fail_json.assert_called_once_with(
            msg='Failed to remove public ip from the server: {id}. '
                'Failed'.format(id=server.id))

    @patch.object(clc_publicip, 'AnsibleModule')
    @patch.object(clc_publicip, 'ClcPublicIp')
    def test_main(self, mock_ClcPublicIp, mock_AnsibleModule):
        mock_ClcPublicIp_instance       = mock.MagicMock()
        mock_AnsibleModule_instance     = mock.MagicMock()
        mock_ClcPublicIp.return_value   = mock_ClcPublicIp_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_publicip.main()

        mock_ClcPublicIp.assert_called_once_with(mock_AnsibleModule_instance)
        assert mock_ClcPublicIp_instance.process_request.call_count == 1


if __name__ == '__main__':
    unittest.main()
