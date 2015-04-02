#!/usr/bin/python

import clc_publicip as clc_publicip
from clc_publicip import ClcPublicIp
import clc as clc_sdk
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
        expected_arg_spec = dict(
            server_ids=dict(type='list', required=True),
            protocol=dict(default='TCP'),
            ports=dict(type='list', required=True)
            )
        under_test = ClcPublicIp.define_argument_spec()
        self.assertDictEqual(expected_arg_spec, under_test)


    @patch.object(ClcPublicIp, 'clc')
    def test_process_request(self, mock_clc_sdk):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2']
            , 'ports': [80]
            , 'protocol': 'TCP'
        }
        # Mock Add IP Requests
        mock_req1 = mock.MagicMock(spec=clc_sdk.v2.Request)
        mock_req2 = mock.MagicMock(spec=clc_sdk.v2.Request)
        # Mock Servers
        mock_server1 = create_autospec(clc_sdk.v2.Server)
        mock_server2 = create_autospec(clc_sdk.v2.Server)
        mock_server1.data = {'details': {'ipAddresses': [{'internal': '1.2.3.4'}]}}
        mock_server1.PublicIPs().public_ips = ['10.10.10.10']
        mock_server1.PublicIPs().Add.return_value = mock_req1
        mock_server2.data = {'details': {'ipAddresses': [{'internal': '5.6.7.8'}]}}
        mock_server2.PublicIPs().public_ips = ['11.11.11.11']
        mock_server2.PublicIPs().Add.return_value = mock_req2
        mock_servers = [mock_server1, mock_server2]
        ClcPublicIp.clc.v2.Servers().servers = mock_servers

        expected_server_result = [
            {'publicip': '10.10.10.10', 'ipaddress': '1.2.3.4', 'details': {'ipAddresses': [{'internal': '1.2.3.4'}]}},
            {'publicip': '11.11.11.11', 'ipaddress': '5.6.7.8', 'details': {'ipAddresses': [{'internal': '5.6.7.8'}]}}
        ]

        under_test = ClcPublicIp(self.module)
        under_test.process_request(test_params)

        self.assertEqual(mock_clc_sdk.v2.Servers.call_count, 3)
        self.module.exit_json.assert_called_once_with(changed=True, servers=expected_server_result, server_ids=test_params['server_ids'])
        self.assertFalse(self.module.fail_json.called)


    @patch.object(clc_publicip, 'AnsibleModule')
    @patch.object(clc_publicip, 'ClcPublicIp')
    def test_main(self, mock_ClcPublicIp, mock_AnsibleModule):
        mock_ClcPublicIp_instance = mock.MagicMock()
        mock_AnsibleModule_instance = mock.MagicMock()
        mock_ClcPublicIp.return_value = mock_ClcPublicIp_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_publicip.main()

        mock_ClcPublicIp.assert_called_once_with(mock_AnsibleModule_instance)
        mock_ClcPublicIp_instance.process_request.assert_called_once_with(mock_AnsibleModule_instance.params)


if __name__ == '__main__':
    unittest.main()
