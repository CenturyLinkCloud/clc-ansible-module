#!/usr/bin/python

import clc_package as clc_package
from clc_package import ClcPackage
import clc as clc_sdk
from clc import CLCException
import mock
from mock import patch
from mock import create_autospec
import unittest

class TestClcPackageFunctions(unittest.TestCase):


    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        reload(clc_package)


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
        # Mock Package
        package1 = mock.MagicMock()
        package2 = mock.MagicMock()
        package1.package_id = '123'
        package1.server_ids = mock_server1
        package1.package_params = {}
        package2.package_id = '123'
        package2.server_ids = mock_server2
        package2.package_params = {}
        return [mock_server1, mock_server2]

    def test_clc_module_not_found(self):
        # Setup Mock Import Function
        import __builtin__ as builtins
        real_import = builtins.__import__
        def mock_import(name, *args):
            if name == 'clc': raise ImportError
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_package)
            clc_package.ClcPackage(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='clc-python-sdk required for this module')


    @patch.object(ClcPackage, 'clc')
    def test_set_clc_creds_w_token(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_TOKEN': 'dummyToken'}):
            under_test = ClcPackage(self.module)
            under_test._set_clc_creds_from_env()
        self.assertEqual(under_test.clc._LOGIN_TOKEN_V2, 'dummyToken')
        self.assertFalse(mock_clc_sdk.v2.SetCredentials.called)
        self.assertEqual(self.module.fail_json.called, False)

    @patch.object(ClcPackage, 'clc')
    def test_set_clc_credentials_w_creds(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'dummyuser', 'CLC_V2_API_PASSWD': 'dummypwd'}):
            under_test = ClcPackage(self.module)
            under_test._set_clc_creds_from_env()
        mock_clc_sdk.v2.SetCredentials.assert_called_once_with(api_username='dummyuser', api_passwd='dummypwd')


    def test_set_clc_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcPackage(self.module)
            under_test._set_clc_creds_from_env()
        self.assertEqual(self.module.fail_json.called, True)


    def test_define_argument_spec(self):
        result = ClcPackage.define_argument_spec()
        self.assertIsInstance(result, dict)

    @patch.object(ClcPackage, 'clc')
    def test_get_servers_from_clc_api(self, mock_clc_sdk):
        mock_clc_sdk.v2.Servers.side_effect = CLCException("Server Not Found")
        under_test = ClcPackage(self.module)
        under_test._get_servers_from_clc(['TESTSVR1', 'TESTSVR2'], 'FAILED TO OBTAIN LIST')
        self.module.fail_json.assert_called_once_with(msg='FAILED TO OBTAIN LIST: Server Not Found')

    @patch.object(ClcPackage, '_set_clc_creds_from_env')
    @patch.object(ClcPackage, 'clc_install_packages')
    def test_process_request_w_valid_args(self, mock_set_clc_creds, mock_install_packages):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2']
            , 'package_id': 'TSTPKGID1'
            , 'package_params': {}
        }
        self.module.params = test_params
        under_test = ClcPackage(self.module)
        under_test.process_request()

        self.assertTrue(mock_set_clc_creds.called)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcPackage, '_set_clc_creds_from_env')
    @patch.object(ClcPackage, 'clc_install_packages')
    def test_process_request_w_no_server_ids(self, mock_set_clc_creds, mock_install_packages):
        test_params = {
            'server_ids': []
            ,'package_id': 'TSTPKGID1'
            , 'package_params': {}
        }
        self.module.params = test_params
        under_test = ClcPackage(self.module)
        under_test.process_request()

        self.assertTrue(mock_set_clc_creds.called)
        self.assertTrue(self.module.fail_json.called)
        self.module.fail_json.assert_called_once_with(msg='Error: server_ids is required')

    @patch.object(ClcPackage, '_set_clc_creds_from_env')
    @patch.object(ClcPackage, 'clc_install_packages')
    def test_process_request_w_no_package_id(self, mock_set_clc_creds, mock_install_packages):
        test_params = {
            'server_ids': ['TESTSVR1, TESTSVR2']
            , 'package_id': ''
            , 'package_params': {}
        }
        self.module.params = test_params
        under_test = ClcPackage(self.module)
        under_test.process_request()

        self.assertTrue(mock_set_clc_creds.called)
        self.assertTrue(self.module.fail_json.called)
        self.module.fail_json.assert_called_once_with(msg='Error: package_id is required')

    @patch.object(ClcPackage, '_get_servers_from_clc')
    def test_clc_install_packages(self, mock_get_servers_from_clc):
        test_params = {
            'server_ids': ['TESTSVR1, TESTSVR2']
            , 'package_id': 'dummyId'
            , 'package_params': {}
        }
        server_ids = ['TESTSVR1, TESTSVR2']
        package_id = 'dummyId'
        package_params = {}
        self.module.params = test_params
        under_test = ClcPackage(self.module)
        under_test.clc_install_packages(server_ids, package_id, package_params)

        self.assertTrue(mock_get_servers_from_clc.called)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_package, 'AnsibleModule')
    @patch.object(clc_package, 'ClcPackage')
    def test_main(self, mock_ClcPackage, mock_AnsibleModule):
        mock_ClcPackage_instance       = mock.MagicMock()
        mock_AnsibleModule_instance     = mock.MagicMock()
        mock_ClcPackage.return_value   = mock_ClcPackage_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_package.main()

        mock_ClcPackage.assert_called_once_with(mock_AnsibleModule_instance)
        mock_ClcPackage_instance.process_request.assert_called_once()


if __name__ == '__main__':
    unittest.main()
