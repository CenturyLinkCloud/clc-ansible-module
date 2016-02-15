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
    def build_mock_server(self):
        # Mock Add IP Requests
        mock_req1 = mock.MagicMock()

        # Mock PublicIps
        pubip1 = mock.MagicMock()
        pubip1.id = '10.10.10.10'
        pubip1.internal = '9.10.11.12'

        # Mock Server
        mock_server1 = mock.MagicMock()
        mock_server2 = mock.MagicMock()
        mock_server1.id = 'TESTSVR1'
        mock_server1.data = {'details': {'ipAddresses': [{'internal': '1.2.3.4'}]}}
        mock_server1.PublicIPs().public_ips = [pubip1]
        pubip1.Delete.return_value = mock_req1
        mock_req1.server = mock_server1
        mock_req1.requests = [mock_req1]
        mock_server1.PublicIPs().Add.return_value = mock_req1
        return mock_server1


    def build_mock_server_wo_public_ips(self):
        mock_server = self.build_mock_server()
        mock_server.PublicIPs().public_ips = []
        return mock_server

    @patch.object(clc_publicip, 'clc_sdk')
    def test_set_user_agent(self, mock_clc_sdk):
        clc_publicip.__version__ = "1"
        ClcPublicIp._set_user_agent(mock_clc_sdk)

        self.assertTrue(mock_clc_sdk.SetRequestsSession.called)

    def build_mock_publicip_add_request(self, mock_server=None, status='succeeded'):
        if mock_server is None:
            mock_server = self.build_mock_server()
        assert mock_server.PublicIPs().Add()\
            , "Mock must contain valid mocked server with a PublicIPs().Add() function"

        mock_request = mock_server.PublicIPs().Add()
        mock_request.Status.return_value = status
        return mock_request


    def build_mock_publicip_delete_request(self, mock_server=None, status = 'succeeded'):
        if mock_server is None:
            mock_server = self.build_mock_server()
        assert mock_server.PublicIPs().public_ips[0].Delete()\
            , "Mock must contain valid mocked server with a PublicIPs().Add() function"

        mock_request = mock_server.PublicIPs().public_ips[0].Delete()
        mock_request.Status.return_value = status
        return mock_request


    def build_mock_server_id(self):
        mock_server = self.build_mock_server()
        return mock_server.id


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
            ClcPublicIp(self.module)

        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='clc-python-sdk required for this module')
        reload(clc_publicip)


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
            reload(clc_publicip)
            ClcPublicIp(self.module)

        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='requests library  version should be >= 2.5.0')
        reload(clc_publicip)

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
            reload(clc_publicip)
            ClcPublicIp(self.module)

        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='requests library is required for this module')
        reload(clc_publicip)

    def test_set_clc_credentials_w_token(self):
        with patch.dict('os.environ', {'CLC_V2_API_TOKEN': 'Token12345',
                                       'CLC_ACCT_ALIAS': 'TEST' }):
            with patch.object(ClcPublicIp, 'clc') as mock_clc_sdk:
                under_test = ClcPublicIp(self.module)
                under_test._set_clc_credentials_from_env()
        self.assertEqual(mock_clc_sdk._LOGIN_TOKEN_V2, 'Token12345')
        self.assertFalse(mock_clc_sdk.v2.SetCredentials.called)
        self.assertEqual(self.module.fail_json.called, False)


    def test_set_clc_credentials_w_creds(self):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'hansolo', 'CLC_V2_API_PASSWD': 'falcon'}):
            with patch.object(ClcPublicIp, 'clc') as mock_clc_sdk:
                under_test = ClcPublicIp(self.module)
                under_test._set_clc_credentials_from_env()
        mock_clc_sdk.v2.SetCredentials.assert_called_once_with(api_username='hansolo', api_passwd='falcon')

    @patch.object(ClcPublicIp, 'clc')
    def test_set_clc_credentials_w_api_url(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_URL': 'dummyapiurl'}):
            under_test = ClcPublicIp(self.module)
            under_test._set_clc_credentials_from_env()
            self.assertEqual(under_test.clc.defaults.ENDPOINT_URL_V2, 'dummyapiurl')


    def test_set_clc_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcPublicIp(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(self.module.fail_json.called, True)


    def test_define_argument_spec(self):
        result = ClcPublicIp._define_module_argument_spec()
        self.assertIsInstance(result, dict)

    def test_wait_for_request_to_complete_req_successful(self):
        mock_request = self.build_mock_publicip_add_request(status='succeeded')
        under_test = ClcPublicIp(self.module)._wait_for_request_to_complete
        under_test(mock_request)
        self.assertFalse(self.module.fail_json.called)


    def test_wait_for_request_to_complete_req_failed(self):
        mock_request = self.build_mock_publicip_add_request(status='failed')
        under_test = ClcPublicIp(self.module)._wait_for_request_to_complete
        under_test(mock_request)
        self.assertTrue(self.module.fail_json.called)


    @patch.object(ClcPublicIp, 'clc')
    def test_get_server_from_clc_api(self, mock_clc_sdk):
        mock_clc_sdk.v2.Server.side_effect = CLCException("Server Not Found")
        under_test = ClcPublicIp(self.module)
        under_test._get_server_from_clc('TESTSVR1', 'FAILED TO OBTAIN SERVER')
        self.module.fail_json.assert_called_once_with(msg='FAILED TO OBTAIN SERVER: Server Not Found')

    @patch.object(ClcPublicIp, 'clc')
    def test_add_publicip_to_server_exception(self, mock_clc_sdk):
        error = CLCException("Failed")
        error.response_text = 'Mock failure message'
        mock_server = mock.MagicMock()
        mock_server.id = 'TESTSVR1'
        mock_server.data = {'details': {'ipAddresses': [{'internal': '1.2.3.4'}]}}
        mock_server.PublicIPs().Add.side_effect = error
        under_test = ClcPublicIp(self.module)
        under_test._add_publicip_to_server(mock_server, 'ports')
        self.module.fail_json.assert_called_once_with(
            msg='Failed to add public ip to the server : TESTSVR1. Mock failure message')

    @patch.object(ClcPublicIp, 'clc')
    def test_remove_publicip_from_server_exception(self, mock_clc_sdk):
        error = CLCException("Failed")
        error.response_text = 'Mock failure message'
        mock_server = mock.MagicMock()
        mock_server.id = 'TESTSVR1'
        ip = mock.MagicMock()
        ip.ipAddresses = [{'internal': '1.2.3.4'}]
        ip.Delete.side_effect = error
        mock_server.data = {'details': ip}
        mock_server.PublicIPs().public_ips = [ip]
        under_test = ClcPublicIp(self.module)
        under_test._remove_publicip_from_server(mock_server)
        self.module.fail_json.assert_called_once_with(
            msg='Failed to remove public ip from the server : TESTSVR1. Mock failure message')

    @patch.object(ClcPublicIp, 'ensure_public_ip_present')
    @patch.object(ClcPublicIp, '_set_clc_credentials_from_env')
    def test_process_request_state_present(self, mock_set_clc_creds, mock_public_ip):
        test_params = {
            'server_id': 'TESTSVR1'
            ,'ports': [
                {'port': 80},
                {'port': 90, 'protocol': 'TCP'}
            ]
            ,'wait': True
            ,'state': 'present'
        }
        mock_public_ip.return_value = True, 'TESTSVR1', mock.MagicMock()
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcPublicIp(self.module)
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(changed=True, server_id='TESTSVR1')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcPublicIp, 'ensure_public_ip_present')
    @patch.object(ClcPublicIp, '_set_clc_credentials_from_env')
    def test_process_request_calls_ensure_public_ip_present_with_expected_args(self, mock_set_clc_creds, mock_public_ip):
        test_params = {
            'server_id': 'TESTSVR1'
            ,'private_ip': '10.11.12.13'
            ,'source_restrictions': ['no']
            ,'ports': [
                {'port': 80},
                {'port': 90, 'protocol': 'TCP'}
            ]
            ,'wait': True
            ,'state': 'present'
        }
        mock_public_ip.return_value = True, 'TESTSVR1', mock.MagicMock()
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcPublicIp(self.module)
        under_test.process_request()

        mock_public_ip.assert_called_once_with(
            server_id='TESTSVR1'
            , private_ip="10.11.12.13"
            , ports=[
                {'port': 80, 'protocol': 'TCP'},
                {'port': 90, 'protocol': 'TCP'}
            ]
            , source_restrictions=['no']
        )
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcPublicIp, 'ensure_public_ip_absent')
    @patch.object(ClcPublicIp, '_set_clc_credentials_from_env')
    def test_process_request_state_absent(self, mock_set_clc_creds, mock_public_ip):
        test_params = {
            'server_id': 'TESTSVR1'
            ,'ports': [
                {'port': 80},
                {'port': 90, 'protocol': 'TCP'}
            ]
            ,'wait': True
            ,'state': 'absent'
        }
        mock_public_ip.return_value = True, 'TESTSVR1', mock.MagicMock()
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcPublicIp(self.module)
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(changed=True, server_id='TESTSVR1')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcPublicIp, '_validate_ports')
    @patch.object(ClcPublicIp, 'ensure_public_ip_present')
    @patch.object(ClcPublicIp, '_set_clc_credentials_from_env')
    def test_process_request_validates_valid_ports_argument(self, mock_set_clc_creds, mock_public_ip, mock_validate_ports):
        test_params = {
            'server_id': 'TESTSVR1'
            ,'ports': [
                {'port': 80},
                {'port': 34590, 'protocol': 'UDP'}
            ]
            ,'wait': True
            ,'state': 'present'
        }
        mock_public_ip.return_value = True, 'TESTSVR1', mock.MagicMock()
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcPublicIp(self.module)
        under_test.process_request()

        mock_validate_ports.assert_called_once_with(test_params['ports'])
        self.module.exit_json.assert_called_once_with(changed=True, server_id='TESTSVR1')
        self.assertFalse(self.module.fail_json.called)

    def test_valid_ports_returns_expected_output(self):
        expected = [
            {'port': 80, 'protocol': 'TCP'},
            {'port': 34590, 'protocol': 'UDP'}
        ]

        input_data = [
            {'port': 80},
            {'port': 34590, 'protocol': 'UDP'}
        ]

        under_test = ClcPublicIp(self.module)
        actual = under_test._validate_ports(input_data)

        self.assertEqual(expected, actual)
        self.assertFalse(self.module.fail_json.called)

    def test_valid_ports_returns_expected_error_for_missing_port(self):
        under_test = ClcPublicIp(self.module)
        under_test._validate_ports([{'protocol': 'UDP'}])

        self.module.fail_json.assert_called_once_with(msg="You must provide a port")

    def test_valid_ports_returns_expected_error_for_invalid_protocol(self):
        under_test = ClcPublicIp(self.module)
        under_test._validate_ports([{'protocol': 'ICP', 'port': 'Faygo'}])

        self.module.fail_json.assert_called_once_with(
            msg="Valid protocols for this module are: [TCP, UDP]: You specified 'ICP'"
        )

    def test_valid_ports_skips_and_removes_blank_entry(self):
        expected = [{'protocol': 'TCP', 'port': 456}]
        under_test = ClcPublicIp(self.module)
        actual = under_test._validate_ports([{'protocol': 'TCP', 'port': 456}, {}])

        self.assertEqual(expected, actual)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcPublicIp, 'ensure_public_ip_absent')
    @patch.object(ClcPublicIp, '_set_clc_credentials_from_env')
    def test_process_request_state_invalid(self, mock_set_clc_creds, mock_public_ip):
        test_params = {
            'server_id': 'TESTSVR1'
            ,'ports': [
                {'port': 80},
                {'port': 90, 'protocol': 'TCP'}
            ]
            ,'wait': True
            ,'state': 'INVALID'
        }

        self.module.params = test_params
        under_test = ClcPublicIp(self.module)
        under_test.process_request()
        self.assertFalse(mock_public_ip.called)
        self.module.fail_json.assert_called_once_with(msg='Unknown State: INVALID')
        self.assertFalse(self.module.exit_json.called)

    @patch.object(ClcPublicIp, '_get_server_from_clc')
    def test_ensure_server_publicip_present_w_mock_server(self,mock_get_server):
        server_id = 'TESTSVR1'
        mock_get_server.return_value=mock.MagicMock()
        ports = [
            {'port': 80},
            {'port': 90, 'protocol': 'TCP'}
        ]
        self.module.check_mode = False
        under_test = ClcPublicIp(self.module)
        under_test.ensure_public_ip_present(server_id, ports)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcPublicIp, '_get_server_from_clc')
    def test_ensure_server_publicip_present_returns_expected_data(self,mock_get_server):
        server_id = 'TESTSVR1'
        mock_server = mock.MagicMock()
        mock_server.id = server_id
        mock_server.PublicIPs().Add.return_value = 'Awesome Result'
        mock_get_server.return_value=mock_server
        ports = [
            {'port': 80},
            {'port': 1290, 'protocol': 'UDP'}
        ]

        self.module.check_mode = False
        under_test = ClcPublicIp(self.module)

        changed, changed_server_id, result = under_test.ensure_public_ip_present(server_id, ports)

        self.assertEqual(True, changed)
        self.assertEqual(server_id, changed_server_id)
        self.assertEqual('Awesome Result', result)

    @patch.object(ClcPublicIp, '_get_server_from_clc')
    def test_ensure_server_publicip_present_w_mock_server_restrictions(self,mock_get_server):
        server_id = 'TESTSVR1'
        mock_get_server.return_value=mock.MagicMock()
        ports = [
            {'port': 80},
            {'port': 1290, 'protocol': 'UDP'}
        ]
        restrictions = ['1.1.1.1/24', '2.2.2.0/36']
        self.module.check_mode = False
        under_test = ClcPublicIp(self.module)
        under_test.ensure_public_ip_present(server_id=server_id,
                                            ports=ports,
                                            source_restrictions=restrictions)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcPublicIp, '_add_publicip_to_server')
    @patch.object(ClcPublicIp, '_get_server_from_clc')
    def test_ensure_server_publicip_present_calls_private_helper_with_expected_args(self,mock_get_server,mock_add_ip):
        server_id = 'TESTSVR1'
        mock_server = mock.MagicMock()
        mock_get_server.return_value=mock_server
        private_ip = '2.4.6.01'
        ports = [
            {'port': 80},
            {'port': 1290, 'protocol': 'UDP'}
        ]
        restrictions = ['not now']
        self.module.check_mode = False
        under_test = ClcPublicIp(self.module)
        under_test.ensure_public_ip_present(server_id=server_id,
                                            private_ip=private_ip,
                                            ports=ports,
                                            source_restrictions=restrictions)
        mock_add_ip.assert_called_once_with(
            mock_server
            , ports
            , private_ip=private_ip
            , source_restrictions=[{'cidr': restrictions[0]}]
        )

    def test_ensure_add_public_ip_to_server_calls_sdk_add_with_expected_args(self):
        mock_server = mock.MagicMock()
        private_ip = '2.4.6.0.1'
        ports = [{'protocol': 'UDP', 'port': 8675309}]
        restrictions = [{'cidr': 'cider'}]
        under_test = ClcPublicIp(self.module)
        under_test._add_publicip_to_server( server=mock_server,
                                            private_ip=private_ip,
                                            ports_to_expose=ports,
                                            source_restrictions=restrictions)
        mock_server.PublicIPs().Add.assert_called_once_with(
            ports=ports
            , private_ip=private_ip
            , source_restrictions=restrictions
        )

    @patch.object(ClcPublicIp, '_get_server_from_clc')
    def test_ensure_server_absent_absent_w_mock_server(self,mock_get_server):
        server_id = ['TESTSVR1']
        mock_server1 = mock.MagicMock()
        mock_server1.id = 'TESTSVR1'
        public_ips_obj = mock.MagicMock()
        ip = mock.MagicMock()
        ip.Delete.return_value = 'success'
        public_ips_obj.public_ips = [ip]
        mock_server1.PublicIPs.return_value = public_ips_obj
        mock_get_server.return_value = mock_server1
        self.module.check_mode = False

        under_test = ClcPublicIp(self.module)
        changed, server_modified, request = under_test.ensure_public_ip_absent(server_id)
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(changed, True)
        self.assertEqual(server_modified, 'TESTSVR1')

    def test_wait_for_request_w_mock_request(self):
        mock_r1 = mock.MagicMock()
        mock_r1.WaitUntilComplete.return_value = True
        self.module.wait = True

        under_test = ClcPublicIp(self.module)
        under_test._wait_for_request_to_complete(mock_r1)
        self.assertFalse(self.module.fail_json.called)

    def test_wait_for_request_w_mock_request_fail(self):
        mock_request = mock.MagicMock()
        mock_request.WaitUntilComplete.return_value = True
        mock_response = mock.MagicMock()
        mock_response.Status.return_value = 'Failed'
        mock_request.requests = [mock_response]
        self.module.wait = True

        under_test = ClcPublicIp(self.module)
        under_test._wait_for_request_to_complete(mock_request)
        self.assertTrue(self.module.fail_json.called)

    @patch.object(ClcPublicIp, '_get_server_from_clc')
    def test_ensure_server_publicip_absent_returns_expected_data(self,mock_get_server):
        server_id = 'TESTSVR1'
        mock_server = mock.MagicMock()
        mock_server.id = server_id
        ip1 = mock.MagicMock()
        ip2 = mock.MagicMock()
        ip1.Delete = mock.MagicMock(return_value="Hell0")
        ip2.Delete = mock.MagicMock(return_value="More Awesome Result")
        mock_server.PublicIPs().public_ips = [ip1, ip2]
        mock_get_server.return_value=mock_server

        self.module.check_mode = False
        under_test = ClcPublicIp(self.module)

        changed, changed_server_id, result = under_test.ensure_public_ip_absent(server_id)

        self.assertEqual(True, changed)
        self.assertEqual(server_id, changed_server_id)
        self.assertEqual('More Awesome Result', result)

    def test_wait_for_request_no_wait(self):
        mock_request = mock.MagicMock()
        mock_request.WaitUntilComplete.return_value = True
        self.module.params = {
            'wait': False
        }
        under_test = ClcPublicIp(self.module)
        under_test._wait_for_request_to_complete(mock_request)
        self.assertFalse(self.module.fail_json.called)


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
