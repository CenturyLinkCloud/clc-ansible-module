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

import mock
from mock import patch
import unittest

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException

import clc_ansible_module.clc_server_snapshot as clc_server_snapshot
from clc_ansible_module.clc_server_snapshot import ClcSnapshot


class TestClcServerSnapshotFunctions(unittest.TestCase):

    def setUp(self):
        self.clc_auth = {'clc_alias': 'mock_alias', 'clc_location': 'mock_dc'}
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()

        server1 = mock.MagicMock()
        server1.id = 'mock_id1'
        server1.data = {
            'details': {
                'snapshots': [
                    {'name': '1',
                     'links': [{
                         'rel': 'self',
                         'href': 'mock_url/snapshots/1'
                     }]}
                ]
            }
        }
        self.mock_server1 = server1

        server2 = mock.MagicMock()
        server2.id = 'mock_id2'
        server2.data = {
            'details': {
                'snapshots': []
            }
        }
        self.mock_server2 = server2

    def test_define_argument_spec(self):
        result = ClcSnapshot.define_argument_spec()
        self.assertIsInstance(result, dict)

    @patch.object(ClcSnapshot, 'ensure_server_snapshot_present')
    @patch.object(clc_common, 'authenticate')
    def test_process_request_state_present(self, mock_authenticate,
                                           mock_server_snapshot):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2'],
            'expiration_days': 7,
            'wait': True,
            'state': 'present',
            'ignore_failures': False
        }
        mock_server_snapshot.return_value = True, mock.MagicMock(), ['TESTSVR1'], []
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcSnapshot(self.module)
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(
            changed=True, server_ids=['TESTSVR1'], failed_server_ids=[])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcSnapshot, 'ensure_server_snapshot_absent')
    @patch.object(clc_common, 'authenticate')
    def test_process_request_state_absent(self, mock_authenticate,
                                          mock_server_snapshot):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2'],
            'expiration_days': 7,
            'wait': True,
            'state': 'absent',
            'ignore_failures': False
        }
        mock_server_snapshot.return_value = True, mock.MagicMock(), ['TESTSVR1','TESTSVR2'], []
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcSnapshot(self.module)
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(changed=True, server_ids=['TESTSVR1', 'TESTSVR2'], failed_server_ids=[])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcSnapshot, 'ensure_server_snapshot_restore')
    @patch.object(clc_common, 'authenticate')
    def test_process_request_state_restore(self, mock_authenticate,
                                           mock_server_snapshot):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2'],
            'expiration_days': 7,
            'wait': True,
            'state': 'restore',
            'ignore_failures': False
        }
        mock_server_snapshot.return_value = True, mock.MagicMock(), ['TESTSVR1'], []
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcSnapshot(self.module)
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(changed=True, server_ids=['TESTSVR1'], failed_server_ids=[])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcSnapshot, 'ensure_server_snapshot_present')
    @patch.object(clc_common, 'authenticate')
    def test_process_request_state_present_partial(self, mock_authenticate,
                                                   mock_server_snapshot):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2'],
            'expiration_days': 7,
            'wait': True,
            'state': 'present',
            'ignore_failures': False
        }
        mock_server_snapshot.return_value = True, mock.MagicMock(), ['TESTSVR1'], ['TESTSVR2']
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcSnapshot(self.module)
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(changed=True, server_ids=['TESTSVR1'], failed_server_ids=['TESTSVR2'])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcSnapshot, 'ensure_server_snapshot_absent')
    @patch.object(clc_common, 'authenticate')
    def test_process_request_state_absent_partial(self, mock_authenticate,
                                                  mock_server_snapshot):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2'],
            'expiration_days': 7,
            'wait': True,
            'state': 'absent',
            'ignore_failures': False
        }
        mock_server_snapshot.return_value = True, mock.MagicMock(), ['TESTSVR2'], ['TESTSVR1']
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcSnapshot(self.module)
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(changed=True, server_ids=['TESTSVR2'], failed_server_ids=['TESTSVR1'])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcSnapshot, 'ensure_server_snapshot_restore')
    @patch.object(clc_common, 'authenticate')
    def test_process_request_state_restore_partial(self, mock_authenticate,
                                                   mock_server_snapshot):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2'],
            'expiration_days': 7,
            'wait': True,
            'state': 'restore',
            'ignore_failures': False
        }
        mock_server_snapshot.return_value = True, mock.MagicMock(), ['TESTSVR1'], ['TESTSVR2']
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcSnapshot(self.module)
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(changed=True, server_ids=['TESTSVR1'], failed_server_ids=['TESTSVR2'])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'servers_by_id')
    @patch.object(ClcSnapshot, '_create_server_snapshot')
    def test_ensure_server_snapshot_present(self, mock_create_snapshot,
                                            mock_get_servers):
        params = {
            'server_ids': [self.mock_server1.id, self.mock_server2.id],
            'expiration_days': 7,
            'ignore_failures': False
        }
        mock_create_snapshot.return_value = mock.MagicMock()
        mock_get_servers.return_value = [self.mock_server1, self.mock_server2]

        self.module.check_mode = False
        under_test = ClcSnapshot(self.module)
        under_test.module.params = params

        changed, request_list, changed_servers, failed_servers = \
            under_test.ensure_server_snapshot_present()

        self.assertTrue(changed)
        self.assertEqual(len(request_list), 1)
        self.assertEqual(changed_servers, [self.mock_server2.id])
        self.assertEqual(failed_servers, [])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'servers_by_id')
    @patch.object(ClcSnapshot, '_create_server_snapshot')
    def test_ensure_server_snapshot_present_ignore_failure(
            self, mock_create_snapshot, mock_get_servers):
        params = {
            'server_ids': [self.mock_server1.id, self.mock_server2.id],
            'expiration_days': 7,
            'ignore_failures': True
        }
        mock_create_snapshot.return_value = None
        mock_get_servers.return_value = [self.mock_server1, self.mock_server2]

        self.module.check_mode = False
        under_test = ClcSnapshot(self.module)
        under_test.module.params = params

        changed, request_list, changed_servers, failed_servers = \
            under_test.ensure_server_snapshot_present()

        self.assertTrue(changed)
        self.assertEqual(len(request_list), 0)
        self.assertEqual(changed_servers, [])
        self.assertEqual(failed_servers, [self.mock_server2.id])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'servers_by_id')
    @patch.object(ClcSnapshot, '_delete_server_snapshot')
    def test_ensure_server_snapshot_absent(
            self, mock_delete_snapshot, mock_get_servers):
        params = {
            'server_ids': [self.mock_server1.id, self.mock_server2.id],
            'expiration_days': 7
        }
        mock_delete_snapshot.return_value = mock.MagicMock()
        mock_get_servers.return_value = [self.mock_server1, self.mock_server2]

        self.module.check_mode = False
        under_test = ClcSnapshot(self.module)
        under_test.module.params = params

        changed, request_list, changed_servers, failed_servers = \
            under_test.ensure_server_snapshot_absent()

        self.assertTrue(changed)
        self.assertEqual(len(request_list), 1)
        self.assertEqual(changed_servers, [self.mock_server1.id])
        self.assertEqual(failed_servers, [])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'servers_by_id')
    @patch.object(ClcSnapshot, '_delete_server_snapshot')
    def test_ensure_server_snapshot_absent_ignore_failure(
            self, mock_delete_snapshot, mock_get_servers):
        params = {
            'server_ids': [self.mock_server1.id, self.mock_server2.id],
            'expiration_days': 7,
            'ignore_failure': True
        }
        mock_delete_snapshot.return_value = None
        mock_get_servers.return_value = [self.mock_server1, self.mock_server2]

        self.module.check_mode = False
        under_test = ClcSnapshot(self.module)
        under_test.module.params = params

        changed, request_list, changed_servers, failed_servers = \
            under_test.ensure_server_snapshot_absent()

        self.assertTrue(changed)
        self.assertEqual(len(request_list), 0)
        self.assertEqual(changed_servers, [])
        self.assertEqual(failed_servers, [self.mock_server1.id])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'servers_by_id')
    @patch.object(ClcSnapshot, '_restore_server_snapshot')
    def test_ensure_server_snapshot_restore(self, mock_restore_snapshot,
                                            mock_get_servers):
        params = {
            'server_ids': [self.mock_server1.id, self.mock_server2.id],
            'expiration_days': 7
        }
        mock_restore_snapshot.return_value = mock.MagicMock()
        mock_get_servers.return_value = [self.mock_server1, self.mock_server2]

        self.module.check_mode = False
        under_test = ClcSnapshot(self.module)
        under_test.module.params = params

        changed, request_list, changed_servers, failed_servers = \
            under_test.ensure_server_snapshot_restore()

        self.assertTrue(changed)
        self.assertEqual(len(request_list), 1)
        self.assertEqual(changed_servers, [self.mock_server1.id])
        self.assertEqual(failed_servers, [])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'servers_by_id')
    @patch.object(ClcSnapshot, '_restore_server_snapshot')
    def test_ensure_server_snapshot_restore_ignore_failure(
            self, mock_restore_snapshot, mock_get_servers):
        params = {
            'server_ids': [self.mock_server1.id, self.mock_server2.id],
            'expiration_days': 7,
            'ignore_failure': True
        }
        mock_restore_snapshot.return_value = None
        mock_get_servers.return_value = [self.mock_server1, self.mock_server2]

        self.module.check_mode = False
        under_test = ClcSnapshot(self.module)
        under_test.module.params = params

        changed, request_list, changed_servers, failed_servers = \
            under_test.ensure_server_snapshot_restore()

        self.assertTrue(changed)
        self.assertEqual(len(request_list), 0)
        self.assertEqual(changed_servers, [])
        self.assertEqual(failed_servers, [self.mock_server1.id])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'wait_on_completed_operations')
    def test_wait_for_requests(self, mock_wait):
        mock_wait.return_value = 1
        under_test = ClcSnapshot(self.module)
        under_test.module.params = {'wait': True}

        under_test._wait_for_requests_to_complete(
            [mock.MagicMock()])

        self.module.fail_json.assert_called_once_with(
            msg='Unable to process server snapshot request')

    def test_wait_for_requests_no_wait(self):
        mock_request = mock.MagicMock()
        self.module.params = {
            'wait': False
        }
        under_test = ClcSnapshot(self.module)
        under_test._wait_for_requests_to_complete([mock_request])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    @patch.object(ClcSnapshot, '_delete_server_snapshot')
    @patch.object(ClcSnapshot, '_wait_for_requests_to_complete')
    def test_create_server_snapshot(self, mock_delete_snapshot,
                                    mock_wait_for_requests, mock_call_api):
        mock_response = mock.MagicMock()
        mock_call_api.return_value = mock_response
        self.module.check_mode = False
        under_test = ClcSnapshot(self.module)
        under_test.clc_auth = self.clc_auth

        result = under_test._create_server_snapshot(self.mock_server1, 7, False)

        self.assertEqual(result, mock_response)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_create_server_snapshot_exception(self, mock_call_api):
        mock_call_api.side_effect = ClcApiException('Failed')
        self.module.check_mode = False
        under_test = ClcSnapshot(self.module)
        under_test.clc_auth = self.clc_auth

        under_test._create_server_snapshot(self.mock_server2, 7, False)

        self.module.fail_json.assert_called_once_with(
            msg='Failed to create snapshot for server: {id}. '
                'Failed'.format(id=self.mock_server2.id))

    @patch.object(clc_common, 'call_clc_api')
    def test_create_server_snapshot_exception_ignore_failure(self, mock_call_api):
        mock_call_api.side_effect = ClcApiException('Failed')
        self.module.check_mode = False
        under_test = ClcSnapshot(self.module)
        under_test.clc_auth = self.clc_auth

        result = under_test._create_server_snapshot(self.mock_server2, 7, True)

        self.assertIsNone(result)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_delete_server_snapshot(self, mock_call_api):
        mock_response = mock.MagicMock()
        mock_call_api.return_value = mock_response
        self.module.check_mode = False
        under_test = ClcSnapshot(self.module)
        under_test.clc_auth = self.clc_auth

        result = under_test._delete_server_snapshot(self.mock_server1, False)

        self.assertEqual(result, mock_response)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_delete_server_snapshot_exception(self, mock_call_api):
        mock_call_api.side_effect = ClcApiException('Failed')
        self.module.check_mode = False
        under_test = ClcSnapshot(self.module)
        under_test.clc_auth = self.clc_auth

        under_test._delete_server_snapshot(self.mock_server1, False)

        self.module.fail_json.assert_called_once_with(
            msg='Failed to delete snapshot for server: {id}. '
                'Failed'.format(id=self.mock_server1.id))

    @patch.object(clc_common, 'call_clc_api')
    def test_delete_server_snapshot_exception_ignore_failure(self, mock_call_api):
        mock_call_api.side_effect = ClcApiException('Failed')
        self.module.check_mode = False
        under_test = ClcSnapshot(self.module)
        under_test.clc_auth = self.clc_auth

        result = under_test._delete_server_snapshot(self.mock_server1, True)

        self.assertIsNone(result)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_restore_server_snapshot(self, mock_call_api):
        mock_response = mock.MagicMock()
        mock_call_api.return_value = mock_response
        self.module.check_mode = False
        under_test = ClcSnapshot(self.module)
        under_test.clc_auth = self.clc_auth

        result = under_test._restore_server_snapshot(self.mock_server1, False)

        self.assertEqual(result, mock_response)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_restore_server_snapshot_exception(self, mock_call_api):
        mock_call_api.side_effect = ClcApiException('Failed')
        self.module.check_mode = False
        under_test = ClcSnapshot(self.module)
        under_test.clc_auth = self.clc_auth

        under_test._restore_server_snapshot(self.mock_server1, False)

        self.module.fail_json.assert_called_once_with(
            msg='Failed to restore snapshot for server: {id}. '
                'Failed'.format(id=self.mock_server1.id))

    @patch.object(clc_common, 'call_clc_api')
    def test_restore_server_snapshot_exception_ignore_failure(
            self, mock_call_api):
        mock_call_api.side_effect = ClcApiException('Failed')
        self.module.check_mode = False
        under_test = ClcSnapshot(self.module)
        under_test.clc_auth = self.clc_auth

        result = under_test._restore_server_snapshot(self.mock_server1, True)

        self.assertIsNone(result)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_server_snapshot, 'AnsibleModule')
    @patch.object(clc_server_snapshot, 'ClcSnapshot')
    def test_main(self, mock_ClcSnapshot, mock_AnsibleModule):
        mock_ClcSnapshot_instance       = mock.MagicMock()
        mock_AnsibleModule_instance     = mock.MagicMock()
        mock_ClcSnapshot.return_value   = mock_ClcSnapshot_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_server_snapshot.main()

        mock_ClcSnapshot.assert_called_once_with(mock_AnsibleModule_instance)
        assert mock_ClcSnapshot_instance.process_request.call_count == 1

if __name__ == '__main__':
    unittest.main()
