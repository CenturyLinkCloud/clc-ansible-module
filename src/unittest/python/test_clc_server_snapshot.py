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

import clc_ansible_module.clc_server_snapshot as clc_server_snapshot
from clc_ansible_module.clc_server_snapshot import ClcSnapshot
import clc as clc_sdk
from clc import CLCException
import mock
from mock import patch
from mock import create_autospec
import unittest

class TestClcServerSnapshotFunctions(unittest.TestCase):


    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        #reload(clc_server_snapshot)

    def test_clc_module_not_found(self):
        # Setup Mock Import Function
        import __builtin__ as builtins
        real_import = builtins.__import__
        def mock_import(name, *args):
            if name == 'clc': raise ImportError
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_server_snapshot)
            ClcSnapshot(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='clc-python-sdk required for this module')

        # Reset
        reload(clc_server_snapshot)

    def test_requests_invalid_version(self):
        # Setup Mock Import Function
        import __builtin__ as builtins
        real_import = builtins.__import__
        def mock_import(name, *args):
            if name == 'requests':
                args[0]['requests'].__version__ = '2.4.0'
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_server_snapshot)
            ClcSnapshot(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='requests library  version should be >= 2.5.0')

        # Reset
        reload(clc_server_snapshot)

    def test_requests_module_not_found(self):
        # Setup Mock Import Function
        import __builtin__ as builtins
        real_import = builtins.__import__
        def mock_import(name, *args):
            if name == 'requests':
                args[0]['requests'].__version__ = '2.7.0'
                raise ImportError
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_server_snapshot)
            ClcSnapshot(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='requests library is required for this module')

        # Reset
        reload(clc_server_snapshot)


    @patch.object(ClcSnapshot, 'clc')
    def test_set_clc_credentials_from_env(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_TOKEN': 'dummyToken',
                                       'CLC_ACCT_ALIAS': 'TEST'}):
            under_test = ClcSnapshot(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(under_test.clc._LOGIN_TOKEN_V2, 'dummyToken')
        self.assertFalse(mock_clc_sdk.v2.SetCredentials.called)
        self.assertEqual(self.module.fail_json.called, False)

    @patch.object(clc_server_snapshot, 'clc_sdk')
    def test_set_user_agent(self, mock_clc_sdk):
        clc_server_snapshot.__version__ = "1"
        ClcSnapshot._set_user_agent(mock_clc_sdk)

        self.assertTrue(mock_clc_sdk.SetRequestsSession.called)

    @patch.object(ClcSnapshot, 'clc')
    def test_set_clc_credentials_w_creds(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'dummyuser', 'CLC_V2_API_PASSWD': 'dummypwd'}):
            under_test = ClcSnapshot(self.module)
            under_test._set_clc_credentials_from_env()
            mock_clc_sdk.v2.SetCredentials.assert_called_once_with(api_username='dummyuser', api_passwd='dummypwd')

    @patch.object(ClcSnapshot, 'clc')
    def test_set_clc_credentials_w_api_url(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_URL': 'dummyapiurl'}):
            under_test = ClcSnapshot(self.module)
            under_test._set_clc_credentials_from_env()
            self.assertEqual(under_test.clc.defaults.ENDPOINT_URL_V2, 'dummyapiurl')

    def test_set_clc_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcSnapshot(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(self.module.fail_json.called, True)


    def test_define_argument_spec(self):
        result = ClcSnapshot.define_argument_spec()
        self.assertIsInstance(result, dict)

    @patch.object(ClcSnapshot, 'ensure_server_snapshot_present')
    @patch.object(ClcSnapshot, '_set_clc_credentials_from_env')
    def test_process_request_state_present(self, mock_set_clc_creds, mock_server_snapshot):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2']
            ,'expiration_days': 7
            ,'wait': True
            , 'state': 'present'
        }
        mock_server_snapshot.return_value = True, mock.MagicMock(), ['TESTSVR1']
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcSnapshot(self.module)
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(changed=True, server_ids=['TESTSVR1'])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcSnapshot, 'ensure_server_snapshot_absent')
    @patch.object(ClcSnapshot, '_set_clc_credentials_from_env')
    def test_process_request_state_absent(self, mock_set_clc_creds, mock_server_snapshot):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2']
            ,'expiration_days': 7
            ,'wait': True
            , 'state': 'absent'
        }
        mock_server_snapshot.return_value = True, mock.MagicMock(), ['TESTSVR1','TESTSVR2']
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcSnapshot(self.module)
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(changed=True, server_ids=['TESTSVR1', 'TESTSVR2'])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcSnapshot, 'ensure_server_snapshot_restore')
    @patch.object(ClcSnapshot, '_set_clc_credentials_from_env')
    def test_process_request_state_restore(self, mock_set_clc_creds, mock_server_snapshot):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2']
            ,'expiration_days': 7
            ,'wait': True
            , 'state': 'restore'
        }
        mock_server_snapshot.return_value = True, mock.MagicMock(), ['TESTSVR1']
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcSnapshot(self.module)
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(changed=True, server_ids=['TESTSVR1'])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcSnapshot, '_get_servers_from_clc')
    def test_ensure_server_snapshot_present_w_mock_server(self,mock_get_servers):
        server_ids = ['TESTSVR1']
        mock_get_servers.return_value=[mock.MagicMock()]
        exp_days = 7
        self.module.check_mode = False
        under_test = ClcSnapshot(self.module)
        under_test.ensure_server_snapshot_present(server_ids, exp_days)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcSnapshot, '_get_servers_from_clc')
    def test_ensure_server_snapshot_absent_w_mock_server(self,mock_get_servers):
        server_ids = ['TESTSVR1']
        mock_server = mock.MagicMock()
        mock_server.id = 'TESTSVR1'
        mock_server.GetSnapshots.return_value = '123'
        mock_get_servers.return_value=[mock_server]
        self.module.check_mode = False

        under_test = ClcSnapshot(self.module)
        under_test.ensure_server_snapshot_absent(server_ids)
        self.assertFalse(self.module.fail_json.called)

    def test_wait_for_requests_w_mock_request(self):
        mock_r1 = mock.MagicMock()
        mock_r1.WaitUntilComplete.return_value = True
        mock_r2 = mock.MagicMock()
        mock_r2.WaitUntilComplete.return_value = True
        requests = [mock_r1, mock_r2]
        self.module.wait = True

        under_test = ClcSnapshot(self.module)
        under_test._wait_for_requests_to_complete(requests)
        self.assertFalse(self.module.fail_json.called)

    def test_wait_for_requests_w_mock_request_fail(self):
        mock_request = mock.MagicMock()
        mock_request.WaitUntilComplete.return_value = True
        mock_response = mock.MagicMock()
        mock_response.Status.return_value = 'Failed'
        mock_request.requests = [mock_response]
        requests = [mock_request]
        self.module.wait = True

        under_test = ClcSnapshot(self.module)
        under_test._wait_for_requests_to_complete(requests)
        self.assertTrue(self.module.fail_json.called)

    @patch.object(ClcSnapshot, '_get_servers_from_clc')
    def test_ensure_server_snapshot_restore_w_mock_server(self,mock_get_servers):
       server_ids = ['TESTSVR1']
       mock_server = mock.MagicMock()
       mock_server.id = 'TESTSVR1'
       mock_server.GetSnapshots.return_value = '123'
       mock_get_servers.return_value=[mock_server]
       self.module.check_mode = False
       under_test = ClcSnapshot(self.module)
       under_test.ensure_server_snapshot_restore(server_ids)
       self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcSnapshot, 'clc')
    def test_get_servers_from_clc(self, mock_clc_sdk):
        mock_clc_sdk.v2.Servers.side_effect = CLCException("Server Not Found")
        under_test = ClcSnapshot(self.module)
        under_test._get_servers_from_clc(['TESTSVR1', 'TESTSVR2'], 'FAILED TO OBTAIN LIST')
        self.module.fail_json.assert_called_once_with(msg='FAILED TO OBTAIN LIST: Server Not Found')

    @patch.object(ClcSnapshot, '_get_servers_from_clc')
    def test_wait_for_requests_to_complete(self,mock_get_servers):
        server_ids = ['INVALID']
        mock_get_servers.return_value=[mock.MagicMock()]
        under_test = ClcSnapshot(self.module)
        under_test._wait_for_requests_to_complete (mock.MagicMock())
        self.assertFalse(self.module.fail_json.called)

    def test_wait_for_requests_no_wait(self):
        mock_request = mock.MagicMock()
        mock_request.WaitUntilComplete.return_value = True
        self.module.params = {
            'wait': False
        }
        under_test = ClcSnapshot(self.module)
        under_test._wait_for_requests_to_complete([mock_request])
        self.assertFalse(self.module.fail_json.called)

    def test_create_server_snapshot_exception(self):
        mock_server = mock.MagicMock()
        mock_server.id = 'test_server'
        error = CLCException('Failed')
        error.response_text = 'Mock failure message'
        mock_server.CreateSnapshot.side_effect = error
        self.module.check_mode = False
        under_test = ClcSnapshot(self.module)
        under_test._create_server_snapshot(mock_server, 10)
        self.module.fail_json.assert_called_once_with(msg='Failed to create snapshot for server : test_server. Mock failure message')

    def test_delete_server_snapshot_exception(self):
        mock_server = mock.MagicMock()
        mock_server.id = 'test_server'
        error = CLCException('Failed')
        error.response_text = 'Mock failure message'
        mock_server.DeleteSnapshot.side_effect = error
        self.module.check_mode = False
        under_test = ClcSnapshot(self.module)
        under_test._delete_server_snapshot(mock_server)
        self.module.fail_json.assert_called_once_with(msg='Failed to delete snapshot for server : test_server. Mock failure message')

    def test_restore_server_snapshot_exception(self):
        mock_server = mock.MagicMock()
        mock_server.id = 'test_server'
        error = CLCException('Failed')
        error.response_text = 'Mock failure message'
        mock_server.RestoreSnapshot.side_effect = error
        self.module.check_mode = False
        under_test = ClcSnapshot(self.module)
        under_test._restore_server_snapshot(mock_server)
        self.module.fail_json.assert_called_once_with(msg='Failed to restore snapshot for server : test_server. Mock failure message')

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
