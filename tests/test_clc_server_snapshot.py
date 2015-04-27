#!/usr/bin/python

import clc_server_snapshot as clc_server_snapshot
from clc_server_snapshot import ClcSnapshot
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
        reload(clc_server_snapshot)


    @patch.object(ClcSnapshot, 'clc')
    def test_set_clc_creds_w_token(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_TOKEN': 'dummyToken'}):
            under_test = ClcSnapshot(self.module)
            under_test._set_clc_creds_from_env()
        self.assertEqual(under_test.clc._LOGIN_TOKEN_V2, 'dummyToken')
        self.assertFalse(mock_clc_sdk.v2.SetCredentials.called)
        self.assertEqual(self.module.fail_json.called, False)

    @patch.object(ClcSnapshot, 'clc')
    def test_set_clc_credentials_w_creds(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'dummyuser', 'CLC_V2_API_PASSWD': 'dummypwd'}):
            under_test = ClcSnapshot(self.module)
            under_test._set_clc_creds_from_env()
            mock_clc_sdk.v2.SetCredentials.assert_called_once_with(api_username='dummyuser', api_passwd='dummypwd')


    def test_set_clc_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcSnapshot(self.module)
            under_test._set_clc_creds_from_env()
        self.assertEqual(self.module.fail_json.called, True)


    def test_define_argument_spec(self):
        result = ClcSnapshot.define_argument_spec()
        self.assertIsInstance(result, dict)

    @patch.object(ClcSnapshot, 'run_clc_commands')
    @patch.object(ClcSnapshot, '_set_clc_creds_from_env')
    def test_process_request_state_present(self, mock_set_clc_creds, mock_run_clc_commands):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2']
            ,'expiration_days': 7
            ,'wait': True
            , 'state': 'present'
        }
        mock_run_clc_commands.return_value = True, ['TESTSVR1']
        self.module.params = test_params

        under_test = ClcSnapshot(self.module)
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(changed=True, servers=['TESTSVR1'])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcSnapshot, 'run_clc_commands')
    @patch.object(ClcSnapshot, '_set_clc_creds_from_env')
    def test_process_request_state_absent(self, mock_set_clc_creds, mock_run_clc_commands):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2']
            ,'expiration_days': 7
            ,'wait': True
            , 'state': 'absent'
        }
        mock_run_clc_commands.return_value = True, ['TESTSVR1','TESTSVR2']
        self.module.params = test_params

        under_test = ClcSnapshot(self.module)
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(changed=True, servers=['TESTSVR1', 'TESTSVR2'])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcSnapshot, 'run_clc_commands')
    @patch.object(ClcSnapshot, '_set_clc_creds_from_env')
    def test_process_request_state_restore(self, mock_set_clc_creds, mock_run_clc_commands):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2']
            ,'expiration_days': 7
            ,'wait': True
            , 'state': 'restore'
        }
        mock_run_clc_commands.return_value = True, ['TESTSVR1']
        self.module.params = test_params

        under_test = ClcSnapshot(self.module)
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(changed=True, servers=['TESTSVR1'])
        self.assertFalse(self.module.fail_json.called)


    @patch.object(ClcSnapshot, 'run_clc_commands')
    @patch.object(ClcSnapshot, '_set_clc_creds_from_env')
    def test_process_request_no_server_ids(self, mock_set_clc_creds, mock_run_clc_commands):
        test_params = {
            'server_ids': None
            ,'expiration_days': 7
            ,'wait': True
            , 'state': 'absent'
        }
        self.module.params = test_params
        mock_run_clc_commands.return_value = True, ['list1'], ['list2']

        under_test = ClcSnapshot(self.module)
        under_test.process_request()

        self.assertTrue(self.module.fail_json.called)
        self.module.fail_json.assert_called_once_with(msg='List of Server ids are required')


    @patch.object(ClcSnapshot, 'run_clc_commands')
    @patch.object(ClcSnapshot, '_set_clc_creds_from_env')
    def test_process_request_state_invalid(self, mock_set_clc_creds, mock_run_clc_commands):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2']
            ,'expiration_days': 7
            ,'wait': True
            , 'state': 'INVALID'
        }

        self.module.params = test_params
        under_test = ClcSnapshot(self.module)
        under_test.process_request()
        self.assertFalse(mock_run_clc_commands.called)
        self.module.fail_json.assert_called_once_with(msg='Unknown State: INVALID')
        self.assertFalse(self.module.exit_json.called)

    @patch.object(ClcSnapshot, 'clc')
    def test_get_servers_from_clc_api(self, mock_clc_sdk):
        mock_clc_sdk.v2.Servers.side_effect = CLCException("Server Not Found")
        under_test = ClcSnapshot(self.module)
        under_test._get_servers_from_clc(['TESTSVR1', 'TESTSVR2'], 'FAILED TO OBTAIN LIST')
        self.module.fail_json.assert_called_once_with(msg='FAILED TO OBTAIN LIST: Server Not Found')

    @patch.object(clc_server_snapshot, 'AnsibleModule')
    @patch.object(clc_server_snapshot, 'ClcSnapshot')
    def test_main(self, mock_ClcSnapshot, mock_AnsibleModule):
        mock_ClcSnapshot_instance       = mock.MagicMock()
        mock_AnsibleModule_instance     = mock.MagicMock()
        mock_ClcSnapshot.return_value   = mock_ClcSnapshot_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_server_snapshot.main()

        mock_ClcSnapshot.assert_called_once_with(mock_AnsibleModule_instance)
        mock_ClcSnapshot_instance.process_request.assert_called_once()


if __name__ == '__main__':
    unittest.main()
