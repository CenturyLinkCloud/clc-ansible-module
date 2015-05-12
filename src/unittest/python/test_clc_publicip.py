#!/usr/bin/python

import clc_ansible_module.clc_publicip as clc_publicip
from clc_ansible_module.clc_publicip import ClcPublicIp
import clc as clc_sdk
from clc import CLCException
import mock
from mock import patch
from mock import create_autospec
import unittest

class TestClcPublicIpFunctions(unittest.TestCase):


    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter=mock.MagicMock()
        reload(clc_publicip)


    #TODO: Put this in a Util/test_data class
    def build_mock_server_list(self):
        # Mock Add IP Requests
        mock_req1 = mock.MagicMock()
        mock_req2 = mock.MagicMock()
        # Mock PublicIps
        pubip1 = mock.MagicMock()
        pubip2 = mock.MagicMock()
        pubip1.id = '10.10.10.10'
        pubip1.internal = '9.10.11.12'
        pubip2.id = '11.11.11.11'
        pubip2.internal = '13.14.15.16'
        # Mock Servers
        mock_server1 = mock.MagicMock()
        mock_server2 = mock.MagicMock()
        mock_server1.id = 'TESTSVR1'
        mock_server1.data = {'details': {'ipAddresses': [{'internal': '1.2.3.4'}]}}
        mock_server1.PublicIPs().public_ips = [pubip1]
        pubip1.Delete.return_value = mock_req1
        mock_req1.server = mock_server1
        mock_req1.requests = [mock_req1]
        mock_server1.PublicIPs().Add.return_value = mock_req1
        mock_server2.id = 'TESTSVR2'
        mock_server2.data = {'details': {'ipAddresses': [{'internal': '5.6.7.8'}]}}
        mock_server2.PublicIPs().public_ips = [pubip2]
        pubip2.Delete.return_value = mock_req2
        mock_req2.server = mock_server2
        mock_req2.requests = [mock_req2]
        mock_server2.PublicIPs().Add.return_value = mock_req2
        return [mock_server1, mock_server2]


    def build_mock_server_list_wo_public_ips(self):
        mock_server_list = self.build_mock_server_list()
        for server in mock_server_list:
            server.PublicIPs().public_ips = []
        return mock_server_list


    def build_mock_publicip_add_request_list(self, mock_server_list=None, status='succeeded'):
        if mock_server_list is None:
            mock_server_list = self.build_mock_server_list()
        assert isinstance(mock_server_list, list), "You must pass a list of mocked servers"
        assert len(mock_server_list) > 0, "You must pass a list of mocked servers with len > 0"
        assert mock_server_list[0].PublicIPs().Add()\
            , "List must contain valid mocked servers with a PublicIPs().Add() function"

        mock_request_list = [server.PublicIPs().Add() for server in mock_server_list]
        for request in mock_request_list:
            request.Status.return_value = status
        return mock_request_list


    def build_mock_publicip_delete_request_list(self, mock_server_list=None, status = 'succeeded'):
        if mock_server_list is None:
            mock_server_list = self.build_mock_server_list()
        assert isinstance(mock_server_list, list), "You must pass a list of mocked servers"
        assert len(mock_server_list) > 0, "You must pass a list of mocked servers with len > 0"
        assert mock_server_list[0].PublicIPs().public_ips[0].Delete()\
            , "List must contain valid mocked servers with a PublicIPs().Add() function"

        mock_request_list = [server.PublicIPs().public_ips[0].Delete() for server in mock_server_list]
        for request in mock_request_list:
            request.Status.return_value = status
        return mock_request_list


    def build_mock_server_id_list(self):
        mock_server_list = self.build_mock_server_list()
        return [server.id for server in mock_server_list]


    def test_clc_module_not_found(self):
        # Setup Mock Import Function
        import __builtin__ as builtins
        real_import = builtins.__import__
        def mock_import(name, *args):
            if name == 'clc': raise ImportError
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_publicip)
            clc_publicip.ClcPublicIp(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='clc-python-sdk required for this module')


    def test_set_clc_credentials_w_token(self):
        with patch.dict('os.environ', {'CLC_V2_API_TOKEN': 'Token12345'}):
            with patch.object(ClcPublicIp, 'clc') as mock_clc_sdk:
                under_test = ClcPublicIp(self.module)
                under_test.set_clc_credentials_from_env()
        self.assertEqual(mock_clc_sdk._LOGIN_TOKEN_V2, 'Token12345')
        self.assertFalse(mock_clc_sdk.v2.SetCredentials.called)
        self.assertEqual(self.module.fail_json.called, False)


    def test_set_clc_credentials_w_creds(self):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'hansolo', 'CLC_V2_API_PASSWD': 'falcon'}):
            with patch.object(ClcPublicIp, 'clc') as mock_clc_sdk:
                under_test = ClcPublicIp(self.module)
                under_test.set_clc_credentials_from_env()
        mock_clc_sdk.v2.SetCredentials.assert_called_once_with(api_username='hansolo', api_passwd='falcon')


    def test_set_clc_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcPublicIp(self.module)
            under_test.set_clc_credentials_from_env()
        self.assertEqual(self.module.fail_json.called, True)


    def test_define_argument_spec(self):
        result = ClcPublicIp.define_argument_spec()
        self.assertIsInstance(result, dict)


    @patch.object(ClcPublicIp, 'run_clc_commands')
    @patch.object(ClcPublicIp, 'set_clc_credentials_from_env')
    def test_process_request_state_present(self, mock_set_clc_creds, mock_run_clc_commands):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2']
            , 'ports': [80]
            , 'protocol': 'TCP'
            , 'state': 'present'
        }
        mock_run_clc_commands.return_value = True, ['list1'], ['list2']

        under_test = ClcPublicIp(self.module)
        under_test.process_request(test_params)

        self.module.exit_json.assert_called_once_with(changed=True, servers=['list1'], server_ids=['list2'])
        self.assertFalse(self.module.fail_json.called)


    @patch.object(ClcPublicIp, 'run_clc_commands')
    @patch.object(ClcPublicIp, 'set_clc_credentials_from_env')
    def test_process_request_state_absent(self, mock_set_clc_creds, mock_run_clc_commands):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2']
            , 'ports': [80]
            , 'protocol': 'TCP'
            , 'state': 'absent'
        }
        mock_run_clc_commands.return_value = True, ['list1'], ['list2']

        under_test = ClcPublicIp(self.module)
        under_test.process_request(test_params)

        self.module.exit_json.assert_called_once_with(changed=True, servers=['list1'], server_ids=['list2'])
        self.assertFalse(self.module.fail_json.called)


    @patch.object(ClcPublicIp, 'run_clc_commands')
    @patch.object(ClcPublicIp, 'set_clc_credentials_from_env')
    def test_process_request_state_invalid(self, mock_set_clc_creds, mock_run_clc_commands):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2']
            , 'ports': [80]
            , 'protocol': 'TCP'
            , 'state': 'NOT_VALID_STATE'
        }

        under_test = ClcPublicIp(self.module)
        under_test.process_request(test_params)

        self.assertFalse(mock_run_clc_commands.called)
        self.module.fail_json.assert_called_once_with(msg='Unknown State: NOT_VALID_STATE')
        self.assertFalse(self.module.exit_json.called)


    @patch.object(ClcPublicIp, 'ip_create_command')
    @patch.object(ClcPublicIp, '_parse_server_results')
    def test_run_clc_commands(self, mock_parse_server_results, mock_ip_create_command):
        mock_servers = self.build_mock_server_list_wo_public_ips()
        mock_request_list = self.build_mock_publicip_add_request_list(mock_server_list=mock_servers)
        mock_ip_create_command.return_value     = mock_request_list, mock_servers
        mock_parse_server_results.return_value = True, mock_servers

        under_test = ClcPublicIp(self.module).run_clc_commands
        result_bool, result_list, result_list2 = under_test([lambda: mock_ip_create_command(server_ids=mock_servers
                                                                                            , protocol='TCP'
                                                                                            , ports=[80, 443])
                                                             ])
        self.assertIsInstance(result_bool, bool)
        self.assertIsInstance(result_list, list)
        self.assertIsInstance(result_list2, list)


    @patch.object(ClcPublicIp, '_get_servers_from_clc_api')
    def test_ip_create_command(self, mock_get_servers_from_clc_api):
        mock_server_list = self.build_mock_server_list_wo_public_ips()
        mock_request_list = self.build_mock_publicip_add_request_list(mock_server_list)
        mock_get_servers_from_clc_api.return_value = mock_server_list

        under_test = ClcPublicIp(self.module).ip_create_command
        requests_lst, servers_to_change = under_test(['TESTSVR1','TESTSVR2'], 'TCP', [80, 443])

        self.assertListEqual(servers_to_change, mock_server_list)
        self.assertListEqual(requests_lst, mock_request_list)


    @patch.object(ClcPublicIp, '_get_servers_from_clc_api')
    def test_ip_delete_command(self, mock_get_servers_from_clc_api):
        mock_server_list = self.build_mock_server_list()
        mock_request_list = self.build_mock_publicip_delete_request_list(mock_server_list=mock_server_list)
        mock_get_servers_from_clc_api.return_value = mock_server_list

        under_test = ClcPublicIp(self.module).ip_delete_command
        requests_lst, servers_to_change = under_test(['TESTSVR1','TESTSVR2'])

        self.assertListEqual(servers_to_change, mock_server_list)
        self.assertListEqual(requests_lst, mock_request_list)


    def test_wait_for_requests_to_complete_req_successful(self):
        mock_request_list = self.build_mock_publicip_add_request_list(status='succeeded')
        under_test = ClcPublicIp(self.module)._wait_for_requests_to_complete
        under_test(mock_request_list)
        self.assertFalse(self.module.fail_json.called)


    def test_wait_for_requests_to_complete_req_failed(self):
        mock_request_list = self.build_mock_publicip_add_request_list(status='failed')
        under_test = ClcPublicIp(self.module)._wait_for_requests_to_complete
        under_test(mock_request_list)
        self.assertTrue(self.module.fail_json.called)


    @patch.object(ClcPublicIp, '_get_servers_from_clc_api')
    def test_refresh_server_public_ips(self, mock_get_servers_from_clc_api):
        mock_server_list = self.build_mock_server_list()
        mock_get_servers_from_clc_api.return_value = mock_server_list

        under_test = ClcPublicIp(self.module)._refresh_server_public_ips
        refreshed_server_ids, refreshed_servers = under_test(mock_server_list)

        self.assertListEqual(refreshed_servers, mock_server_list)
        self.assertListEqual(refreshed_server_ids, ['TESTSVR1', 'TESTSVR2'])


    def test_parse_server_results(self):
        mock_server_list = self.build_mock_server_list()

        under_test = ClcPublicIp(self.module)._parse_server_results
        changed, servers_result = under_test(mock_server_list)

        expected_result = [
            {'public_ip': '10.10.10.10', 'internal_ip': '9.10.11.12', 'ipaddress': '1.2.3.4', 'details': {'ipAddresses': [{'internal': '1.2.3.4'}]}},
            {'public_ip': '11.11.11.11', 'internal_ip': '13.14.15.16', 'ipaddress': '5.6.7.8', 'details': {'ipAddresses': [{'internal': '5.6.7.8'}]}}
        ]
        self.assertTrue(changed)
        self.assertListEqual(servers_result, expected_result)


    @patch.object(ClcPublicIp, 'clc')
    def test_get_servers_from_clc_api(self, mock_clc_sdk):
        mock_clc_sdk.v2.Servers.side_effect = CLCException("Server Not Found")
        under_test = ClcPublicIp(self.module)
        under_test._get_servers_from_clc_api(['TESTSVR1', 'TESTSVR2'], 'FAILED TO OBTAIN LIST')
        self.module.fail_json.assert_called_once_with(msg='FAILED TO OBTAIN LIST: Server Not Found')


    @patch.object(clc_publicip, 'AnsibleModule')
    @patch.object(clc_publicip, 'ClcPublicIp')
    def test_main(self, mock_ClcPublicIp, mock_AnsibleModule):
        mock_ClcPublicIp_instance       = mock.MagicMock()
        mock_AnsibleModule_instance     = mock.MagicMock()
        mock_ClcPublicIp.return_value   = mock_ClcPublicIp_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_publicip.main()

        mock_ClcPublicIp.assert_called_once_with(mock_AnsibleModule_instance)
        mock_ClcPublicIp_instance.process_request.assert_called_once_with(mock_AnsibleModule_instance.params)


if __name__ == '__main__':
    unittest.main()
