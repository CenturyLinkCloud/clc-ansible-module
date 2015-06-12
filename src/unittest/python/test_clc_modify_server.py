#!/usr/bin/python

import unittest

from uuid import UUID
import clc as clc_sdk
from clc import CLCException
from clc import APIFailedResponse
import socket
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
            'state': 'present',
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
    def test_process_request_state_update_cpu_memory_aapolicy(self,
                                          mock_clc_sdk,
                                          mock_set_clc_creds):
        # Setup Test
        self.module.params = {
            'state': 'present',
            'server_ids': ['TEST_SERVER'],
            'cpu': 2,
            'anti_affinity_policy_id': 123,
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
            'state': 'present',
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
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcModifyServer, '_set_clc_credentials_from_env')
    @patch.object(clc_modify_server, 'clc_sdk')
    def test_process_request_state_update_memory(self,
                                          mock_clc_sdk,
                                          mock_set_clc_creds):
        # Setup Test
        self.module.params = {
            'state': 'present',
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
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcModifyServer, '_set_clc_credentials_from_env')
    @patch.object(clc_modify_server, 'clc_sdk')
    def test_process_request_state_update_empty_server_list(self,
                                          mock_clc_sdk,
                                          mock_set_clc_creds):
        # Setup Test
        self.module.params = {
            'state': 'present',
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
            'state': 'present',
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

    def test_push_metric(self):
        ClcModifyServer.STATSD_HOST = '1.1.1.1'
        ClcModifyServer._push_metric('dummy',0)
        pass

    @patch.object(clc_modify_server, 'clc_sdk')
    def test_modify_clc_server_with_empty_server_id(self, mock_clc_sdk):
        # Test
        under_test = ClcModifyServer(self.module)
        under_test._modify_clc_server(self.clc, self.module, 'TEST', None, 1, 2)

        # Assert
        self.assertTrue(self.module.fail_json.called)
        self.module.fail_json.assert_called_once_with(msg='server_id must be provided to modify the server')

    @patch.object(clc_modify_server, 'clc_sdk')
    def test_modify_clc_server_mock_server(self,
                                          mock_clc_sdk):
        # Setup Test
        self.module.params = {
            'state': 'present',
            'server_ids': ['TEST_SERVER'],
            'cpu': 2,
            'memory': 4,
            'wait': True
        }

        mock_server = mock.MagicMock()
        mock_server.id = 'TEST_SERVER'
        mock_server.cpu = 2
        mock_server.memory= 4

        mock_clc_sdk.v2.Server = [mock_server]

        # Test
        self.module.check_mode = False;
        under_test = ClcModifyServer(self.module)
        result = under_test._modify_clc_server(self.clc, self.module, 'WFAD', 'TEST_SERVER', 2, 4)

        # Assert
        self.assertFalse(self.module.fail_json.called)
        self.assertIsNotNone(result)

    @patch.object(clc_modify_server, 'clc_sdk')
    def test_get_anti_affinity_policy_id_by_name_singe_match(self, mock_clc_sdk):
        mock_clc_sdk.v2.API.Call.side_effect = [{'items' :
                                                [{'name' : 'test1', 'id' : '111'},
                                                 {'name' : 'test2', 'id' : '222'}]}]

        policy_id = ClcModifyServer._get_aa_policy_id_by_name(mock_clc_sdk, None, 'alias', 'test1')
        self.assertEqual('111', policy_id)

    @patch.object(clc_modify_server, 'AnsibleModule')
    @patch.object(clc_modify_server, 'clc_sdk')
    def test_get_anti_affinity_policy_id_by_name_no_match(self, mock_clc_sdk, mock_ansible_module):
        mock_clc_sdk.v2.API.Call.side_effect = [{'items' :
                                                [{'name' : 'test1', 'id' : '111'},
                                                 {'name' : 'test2', 'id' : '222'}]}]

        policy_id = ClcModifyServer._get_aa_policy_id_by_name(mock_clc_sdk,
                                                              mock_ansible_module,
                                                              'alias',
                                                              'testnone')
        mock_ansible_module.fail_json.assert_called_with(
            msg='No anti affinity policy was found with policy name : testnone')

    @patch.object(clc_modify_server, 'AnsibleModule')
    @patch.object(clc_modify_server, 'clc_sdk')
    def test_get_anti_affinity_policy_id_by_name_duplicate_match(self, mock_clc_sdk, mock_ansible_module):
        mock_clc_sdk.v2.API.Call.side_effect = [{'items' :
                                                [{'name' : 'test1', 'id' : '111'},
                                                 {'name' : 'test2', 'id' : '222'},
                                                 {'name' : 'test1', 'id' : '111'}]}]

        policy_id = ClcModifyServer._get_aa_policy_id_by_name(mock_clc_sdk,
                                                              mock_ansible_module,
                                                              'alias',
                                                              'test1')
        mock_ansible_module.fail_json.assert_called_with(
            msg='mutiple anti affinity policies were found with policy name : test1')

if __name__ == '__main__':
    unittest.main()
