#!/usr/bin/python

import unittest

from uuid import UUID
import clc as clc_sdk
from clc import CLCException
from clc import APIFailedResponse
import mock
from mock import patch, create_autospec

import clc_ansible_module.clc_modify_server as clc_modify_server
from clc_ansible_module.clc_modify_server import ClcModifyServer


class TestClcModifyServerFunctions(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter = mock.MagicMock()

    def test_clc_module_not_found(self):
        # Setup Mock Import Function
        import __builtin__ as builtins
        real_import = builtins.__import__
        def mock_import(name, *args):
            if name == 'clc': raise ImportError
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_modify_server)
            clc_modify_server.ClcModifyServer(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='clc-python-sdk required for this module')

        # Reset clc_group
        reload(clc_modify_server)

    @patch.object(ClcModifyServer, '_set_clc_credentials_from_env')
    @patch.object(clc_modify_server, 'clc_sdk')
    def test_process_request_state_update_cpu_memory(self,
                                          mock_clc_sdk,
                                          mock_set_clc_creds):
        # Setup Test
        self.module.params = {
            'state': 'update',
            'server_ids': ['TEST_SERVER'],
            'cpu': 2,
            'memory': 4,
            'wait': True
        }

        mock_server = mock.MagicMock()
        mock_server.id = 'TEST_SERVER'
        mock_server.cpu = 2
        mock_server.memory= 2

        mock_clc_sdk.v2.Servers().Servers.return_value = [mock_server]

        # Test
        under_test = ClcModifyServer(self.module)
        under_test.process_request()

        # Assert
        self.assertTrue(self.module.exit_json.called)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcModifyServer, '_set_clc_credentials_from_env')
    @patch.object(clc_modify_server, 'clc_sdk')
    def test_process_request_state_update_cpu(self,
                                          mock_clc_sdk,
                                          mock_set_clc_creds):
        # Setup Test
        self.module.params = {
            'state': 'update',
            'server_ids': ['TEST_SERVER'],
            'cpu': 2,
            'wait': True
        }

        mock_server = mock.MagicMock()
        mock_server.id = 'TEST_SERVER'
        mock_server.cpu = 2
        mock_server.memory= 4

        mock_clc_sdk.v2.Servers().Servers.return_value = [mock_server]

        # Test
        under_test = ClcModifyServer(self.module)
        under_test.process_request()

        # Assert
        self.assertTrue(self.module.exit_json.called)
        self.assertTrue(self.module.fail_json.called)

    @patch.object(ClcModifyServer, '_set_clc_credentials_from_env')
    @patch.object(clc_modify_server, 'clc_sdk')
    def test_process_request_state_update_memory(self,
                                          mock_clc_sdk,
                                          mock_set_clc_creds):
        # Setup Test
        self.module.params = {
            'state': 'update',
            'server_ids': ['TEST_SERVER'],
            'memory': 2,
            'wait': True
        }

        mock_server = mock.MagicMock()
        mock_server.id = 'TEST_SERVER'
        mock_server.cpu = 2
        mock_server.memory= 4

        mock_clc_sdk.v2.Servers().Servers.return_value = [mock_server]

        # Test
        under_test = ClcModifyServer(self.module)
        under_test.process_request()

        # Assert
        self.assertTrue(self.module.exit_json.called)
        self.assertTrue(self.module.fail_json.called)

    @patch.object(ClcModifyServer, '_set_clc_credentials_from_env')
    @patch.object(clc_modify_server, 'clc_sdk')
    def test_process_request_state_update_empty_server_list(self,
                                          mock_clc_sdk,
                                          mock_set_clc_creds):
        # Setup Test
        self.module.params = {
            'state': 'update',
            'server_ids': None,
            'cpu': 2,
            'memory': 4,
            'wait': True
        }

        mock_server = mock.MagicMock()
        mock_server.id = 'TEST_SERVER'
        mock_server.cpu = 2
        mock_server.memory= 2

        #mock_clc_sdk.v2.Servers().Servers.return_value = [mock_server]

        # Test
        under_test = ClcModifyServer(self.module)
        under_test.process_request()

        # Assert
        self.assertFalse(self.module.exit_json.called)
        self.assertTrue(self.module.fail_json.called)
        self.module.fail_json.assert_called_once_with(
            msg='server_ids needs to be a list of instances to modify: None'
        )

    @patch.object(ClcModifyServer, '_set_clc_credentials_from_env')
    @patch.object(clc_modify_server, 'clc_sdk')
    def test_process_request_state_update_same_data(self,
                                          mock_clc_sdk,
                                          mock_set_clc_creds):
        # Setup Test
        self.module.params = {
            'state': 'update',
            'server_ids': ['TEST_SERVER'],
            'cpu': 2,
            'memory': 4,
            'wait': True
        }

        mock_server = mock.MagicMock()
        mock_server.id = 'TEST_SERVER'
        mock_server.cpu = 2
        mock_server.memory= 4

        mock_clc_sdk.v2.Servers().Servers.return_value = [mock_server]

        # Test
        under_test = ClcModifyServer(self.module)
        under_test.process_request()

        # Assert
        self.assertTrue(self.module.exit_json.called)
        self.module.exit_json.assert_called_once_with(changed=False, servers=[], server_ids=[])
        self.assertFalse(self.module.fail_json.called)

    def test_clc_set_credentials_w_creds(self):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'hansolo', 'CLC_V2_API_PASSWD': 'falcon'}):
            with patch.object(clc_modify_server, 'clc_sdk') as mock_clc_sdk:
                under_test = ClcModifyServer(self.module)
                under_test._set_clc_credentials_from_env()

        mock_clc_sdk.v2.SetCredentials.assert_called_once_with(api_username='hansolo', api_passwd='falcon')


    def test_clc_set_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcModifyServer(self.module)
            under_test._set_clc_credentials_from_env()

        self.assertEqual(self.module.fail_json.called, True)

    def test_define_argument_spec(self):
        result = ClcModifyServer._define_module_argument_spec()
        self.assertIsInstance(result, dict)

    @patch.object(clc_modify_server, 'AnsibleModule')
    @patch.object(clc_modify_server, 'ClcModifyServer')
    def test_main(self, mock_ClcModifyServer, mock_AnsibleModule):
        mock_ClcModifyServer_instance          = mock.MagicMock()
        mock_AnsibleModule_instance      = mock.MagicMock()
        mock_ClcModifyServer.return_value      = mock_ClcModifyServer_instance
        mock_AnsibleModule.return_value  = mock_AnsibleModule_instance

        clc_modify_server.main()

        mock_ClcModifyServer.assert_called_once_with(mock_AnsibleModule_instance)
        mock_ClcModifyServer_instance.process_request.assert_called_once

if __name__ == '__main__':
    unittest.main()
