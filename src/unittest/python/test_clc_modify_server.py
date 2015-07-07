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

    @patch.object(clc_modify_server, 'clc_sdk')
    def test_set_user_agent(self, mock_clc_sdk):
        clc_modify_server.__version__ = "1"
        ClcModifyServer._set_user_agent(mock_clc_sdk)

        self.assertTrue(mock_clc_sdk.SetRequestsSession.called)

    @patch.object(ClcModifyServer, '_set_clc_credentials_from_env')
    @patch.object(clc_modify_server, 'clc_sdk')
    def test_process_request_state_present_cpu_memory(self,
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
    def test_process_request_state_present_cpu_memory_aapolicy(self,
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
    def test_process_request_state_present_cpu_memory_alertpolicy(self,
                                          mock_clc_sdk,
                                          mock_set_clc_creds):
        # Setup Test
        self.module.params = {
            'state': 'present',
            'server_ids': ['TEST_SERVER'],
            'cpu': 2,
            'alert_policy_name': 'test',
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
    def test_process_request_state_absent_alertpolicy(self,
                                          mock_clc_sdk,
                                          mock_set_clc_creds):
        # Setup Test
        self.module.params = {
            'state': 'absent',
            'server_ids': ['TEST_SERVER'],
            'cpu': 2,
            'alert_policy_name': 'test',
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
    def test_process_request_state_present_cpu(self,
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
    def test_process_request_state_present_memory(self,
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
    def test_process_request_state_present_empty_server_list(self,
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
    def test_process_request_state_present_same_data(self,
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

    def test_override_v2_api_url_from_environment(self):
        original_url = clc_sdk.defaults.ENDPOINT_URL_V2
        under_test = ClcModifyServer(self.module)

        under_test._set_clc_credentials_from_env()
        self.assertEqual(clc_sdk.defaults.ENDPOINT_URL_V2, original_url)

        with patch.dict('os.environ', {'CLC_V2_API_URL': 'http://unittest.example.com/'}):
            under_test._set_clc_credentials_from_env()

        self.assertEqual(clc_sdk.defaults.ENDPOINT_URL_V2, 'http://unittest.example.com/')

        clc_sdk.defaults.ENDPOINT_URL_V2 = original_url

    @patch.object(ClcModifyServer, 'clc')
    def test_set_clc_credentials_from_env(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_TOKEN': 'dummyToken',
                                       'CLC_ACCT_ALIAS': 'TEST'}):
            under_test = ClcModifyServer(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(under_test.clc._LOGIN_TOKEN_V2, 'dummyToken')
        self.assertFalse(mock_clc_sdk.v2.SetCredentials.called)
        self.assertEqual(self.module.fail_json.called, False)

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

    @patch.object(clc_modify_server, 'clc_sdk')
    def test_get_alert_policy_id_by_name_singe_match(self, mock_clc_sdk):
        mock_clc_sdk.v2.API.Call.side_effect = [{'items' :
                                                [{'name' : 'test1', 'id' : '111'},
                                                 {'name' : 'test2', 'id' : '222'}]}]

        policy_id = ClcModifyServer._get_alert_policy_id_by_name(mock_clc_sdk, None, 'alias', 'test1')
        self.assertEqual('111', policy_id)

    @patch.object(clc_modify_server, 'AnsibleModule')
    @patch.object(clc_modify_server, 'clc_sdk')
    def test_get_alert_policy_id_by_name_no_match(self, mock_clc_sdk, mock_ansible_module):
        mock_clc_sdk.v2.API.Call.side_effect = [{'items' :
                                                [{'name' : 'test1', 'id' : '111'},
                                                 {'name' : 'test2', 'id' : '222'}]}]

        policy_id = ClcModifyServer._get_alert_policy_id_by_name(mock_clc_sdk,
                                                              mock_ansible_module,
                                                              'alias',
                                                              'testnone')
        self.assertEqual(policy_id, None)

    @patch.object(clc_modify_server, 'AnsibleModule')
    @patch.object(clc_modify_server, 'clc_sdk')
    def test_get_aalert_policy_id_by_name_duplicate_match(self, mock_clc_sdk, mock_ansible_module):
        mock_clc_sdk.v2.API.Call.side_effect = [{'items' :
                                                [{'name' : 'test1', 'id' : '111'},
                                                 {'name' : 'test2', 'id' : '222'},
                                                 {'name' : 'test1', 'id' : '111'}]}]

        policy_id = ClcModifyServer._get_alert_policy_id_by_name(mock_clc_sdk,
                                                              mock_ansible_module,
                                                              'alias',
                                                              'test1')
        mock_ansible_module.fail_json.assert_called_with(
            msg='mutiple alert policies were found with policy name : test1')


    @patch.object(clc_modify_server, 'clc_sdk')
    def test_wait_for_requests(self, mock_clc_sdk):
        try:
            servers = mock.MagicMock()
            requests = mock.MagicMock()
            under_test = ClcModifyServer(self.module)
            under_test._wait_for_requests(mock_clc_sdk, requests, servers, True)
        except:
            self.fail('Caught an unexpected exception')
    '''
    @patch.object(ClcModifyServer, '_alert_policy_exists')
    @patch.object(ClcModifyServer, '_add_alert_policy_to_server')
    @patch.object(ClcModifyServer, '_get_alert_policy_id_by_name')
    @patch.object(clc_modify_server, 'AnsibleModule')
    @patch.object(clc_modify_server, 'clc_sdk')
    def test_ensure_server_alert_policy_present_changed(self,
                                  mock_clc_sdk,
                                  mock_ansible_module,
                                  mock_get_alert_pol,
                                  mock_add_alert_pol,
                                  mock_alert_pol_exists):
        mock_alert_pol_exists.return_value = False
        mock_add_alert_pol.return_value = 'OK'
        mock_get_alert_pol.return_value = '123'
        under_test = ClcModifyServer(mock_ansible_module)
        server_params = {
            'alert_policy_name': 'test'
        }
        server = mock.MagicMock()
        server.id = 'server1'
        changed, changed_servers = under_test._ensure_alert_policy_present(
            clc=mock_clc_sdk,
            module=mock_ansible_module,
            acct_alias='alias',
            server=server,
            server_params=server_params)
        self.assertEqual(changed, True)
        self.assertEqual(changed_servers[0].id, 'server1')
    '''
    @patch.object(clc_modify_server, 'AnsibleModule')
    @patch.object(clc_modify_server, 'clc_sdk')
    def test_add_alert_policy(self, mock_clc_sdk, mock_ansible_module):
        mock_clc_sdk.v2.API.Call.side_effect = {'success'}
        mock_ansible_module.check_mode = False
        under_test = ClcModifyServer(mock_ansible_module)
        res = under_test._add_alert_policy_to_server(mock_clc_sdk, mock_ansible_module, 'alias', 'server_id', 'alert_pol_id')
        self.assertEqual(res, 'success')

    @patch.object(clc_modify_server, 'AnsibleModule')
    @patch.object(clc_modify_server, 'clc_sdk')
    def test_add_alert_policy_exception(self, mock_clc_sdk, mock_ansible_module):
        mock_clc_sdk.v2.API.Call.side_effect = Exception('failed')
        mock_ansible_module.check_mode = False
        under_test = ClcModifyServer(mock_ansible_module)
        self.assertRaises(Exception,
                          under_test._add_alert_policy_to_server,
                          mock_clc_sdk,
                          mock_ansible_module,
                          'alias',
                          'server_id',
                          'alert_pol_id')

    @patch.object(clc_modify_server, 'AnsibleModule')
    @patch.object(clc_modify_server, 'clc_sdk')
    def test_remove_alert_policy(self, mock_clc_sdk, mock_ansible_module):
        mock_clc_sdk.v2.API.Call.side_effect = {'success'}
        mock_ansible_module.check_mode = False
        under_test = ClcModifyServer(mock_ansible_module)
        res = under_test._remove_alert_policy_to_server(mock_clc_sdk,
                                                        mock_ansible_module,
                                                        'alias',
                                                        'server_id',
                                                        'alert_pol_id')
        self.assertEqual(res, 'success')

    @patch.object(clc_modify_server, 'AnsibleModule')
    @patch.object(clc_modify_server, 'clc_sdk')
    def test_remove_alert_policy_exception(self, mock_clc_sdk, mock_ansible_module):
        mock_clc_sdk.v2.API.Call.side_effect = Exception('failed')
        mock_ansible_module.check_mode = False
        under_test = ClcModifyServer(mock_ansible_module)
        self.assertRaises(Exception,
                          under_test._remove_alert_policy_to_server,
                          mock_clc_sdk,
                          mock_ansible_module,
                          'alias',
                          'server_id',
                          'alert_pol_id')

    def test_alert_policy_exists_true(self):
        server = mock.MagicMock()
        server.alertPolicies = [{'id': 123, 'name': 'test'}]
        under_test = ClcModifyServer(self.module)
        res = under_test._alert_policy_exists(server, 123)
        self.assertEqual(res, True)

    def test_alert_policy_exists_false(self):
        server = mock.MagicMock()
        server.alertPolicies = [{'id': 123, 'name': 'test'}]
        under_test = ClcModifyServer(self.module)
        res = under_test._alert_policy_exists(server, 111)
        self.assertEqual(res, False)


if __name__ == '__main__':
    unittest.main()
