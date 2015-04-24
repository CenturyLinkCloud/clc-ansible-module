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


if __name__ == '__main__':
    unittest.main()
